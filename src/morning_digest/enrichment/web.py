from dataclasses import replace
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from morning_digest.domain import Article


class ArticleEnricher:
    def enrich(self, article: Article) -> Article:
        content = self._text(article.content)
        if len(content) >= 500:
            return replace(article, content=content)
        request = Request(article.canonical_url, headers={"User-Agent": "MorningDigest/0.1"})
        with urlopen(request, timeout=20) as response:
            html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        content = self._text(html)
        if len(content) < 200:
            raise ValueError("Article body is too short for meaningful analysis")
        return replace(article, content=content)

    @staticmethod
    def _text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for node in soup(["script", "style", "nav", "footer"]):
            node.decompose()
        return " ".join(soup.get_text(" ", strip=True).split())
