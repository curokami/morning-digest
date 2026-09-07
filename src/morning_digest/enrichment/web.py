from dataclasses import replace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from morning_digest.domain import Article


class ArticleAccessError(RuntimeError):
    """Retrieval failure with a cautious, evidence-based classification."""

    def __init__(self, message: str, classification: str, status: int,
                 evidence: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.classification = classification
        self.status = status
        self.evidence = evidence


class ArticleEnricher:
    MINIMUM_CONTENT_LENGTH = 200

    def enrich(self, article: Article) -> Article:
        content = self._text(article.content)
        if len(content) >= self.MINIMUM_CONTENT_LENGTH:
            return replace(article, content=content)
        request = Request(article.canonical_url, headers={"User-Agent": "MorningDigest/0.1"})
        try:
            with urlopen(request, timeout=20) as response:
                html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        except HTTPError as exc:
            body = exc.read(65_536).decode("utf-8", errors="replace")
            classification, evidence = self.classify_denial(exc.code, exc.headers, body)
            details = ",".join(evidence) if evidence else "none"
            raise ArticleAccessError(
                f"Article retrieval denied: status={exc.code} "
                f"classification={classification} evidence={details}",
                classification=classification, status=exc.code, evidence=evidence,
            ) from exc
        content = self._text(html)
        if len(content) < self.MINIMUM_CONTENT_LENGTH:
            raise ValueError("Article body is too short for meaningful analysis")
        return replace(article, content=content)

    @staticmethod
    def _text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for node in soup(["script", "style", "nav", "footer"]):
            node.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())

    @staticmethod
    def classify_denial(status: int, headers, body: str) -> tuple[str, tuple[str, ...]]:
        normalized_headers = {key.lower(): value.lower() for key, value in headers.items()}
        normalized_body = body.lower()
        evidence: list[str] = []

        if normalized_headers.get("server") == "cloudflare":
            evidence.append("server:cloudflare")
        if "cf-ray" in normalized_headers:
            evidence.append("header:cf-ray")
        if normalized_headers.get("cf-mitigated") == "challenge":
            evidence.append("header:cf-mitigated=challenge")

        challenge_markers = {
            "captcha": "body:captcha",
            "challenge-platform": "body:challenge-platform",
            "verify you are human": "body:verify-human",
            "just a moment": "body:just-a-moment",
        }
        for marker, label in challenge_markers.items():
            if marker in normalized_body:
                evidence.append(label)

        if any(item.startswith("header:cf-mitigated") or item.startswith("body:") for item in evidence):
            return "bot_protection_suspected", tuple(evidence)

        auth_markers = ("sign in to continue", "member-only story", "subscription required")
        if status == 401 or any(marker in normalized_body for marker in auth_markers):
            return "authentication_required", tuple(evidence)
        if status == 403:
            return "forbidden_unknown", tuple(evidence)
        return "http_error", tuple(evidence)
