from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class MediumDigestArticleCandidate:
    title: str
    canonical_url: str
    author: str | None
    summary: str
    clap_count: int | None = None


def extract_first_article(html: str) -> MediumDigestArticleCandidate | None:
    """Extract the first article card from a Medium Daily Digest HTML body."""
    return next(iter(extract_articles(html)), None)


def extract_articles(html: str) -> list[MediumDigestArticleCandidate]:
    """Extract unique article cards in their Medium Daily Digest order."""
    document = BeautifulSoup(html, "html.parser")
    candidates: list[MediumDigestArticleCandidate] = []
    seen_urls: set[str] = set()
    for heading in document.find_all("h2"):
        candidate = _article_candidate(heading)
        if candidate is None or candidate.canonical_url in seen_urls:
            continue
        seen_urls.add(candidate.canonical_url)
        candidates.append(candidate)
    return candidates


def _article_candidate(heading) -> MediumDigestArticleCandidate | None:
    article_link = heading.find_parent("a", href=True)
    if article_link is None or not _is_medium_article_url(article_link["href"]):
        return None

    summary_heading = article_link.find("h3")
    return MediumDigestArticleCandidate(
        title=_normalized_text(heading),
        canonical_url=_without_tracking(article_link["href"]),
        author=_find_author(heading, article_link["href"]),
        summary=_normalized_text(summary_heading) if summary_heading else "",
        clap_count=_find_clap_count(heading),
    )


def _find_clap_count(heading) -> int | None:
    for container in heading.parents:
        icon = container.find(
            "img",
            alt=lambda value: isinstance(value, str) and value.casefold() == "claps",
        )
        if icon is not None:
            return _metric_after_icon(icon)
    return None


def _metric_after_icon(icon) -> int | None:
    for element in icon.next_elements:
        if getattr(element, "name", None) == "img":
            alt = element.get("alt", "")
            if isinstance(alt, str) and alt.casefold() == "responses":
                return None
        if isinstance(element, str):
            parsed = _parse_abbreviated_count(element)
            if parsed is not None:
                return parsed
    return None


def _parse_abbreviated_count(value: str) -> int | None:
    match = re.fullmatch(r"\s*([\d,]+(?:\.\d+)?)\s*([kKmM]?)\s*", value)
    if match is None:
        return None
    number = float(match.group(1).replace(",", ""))
    scale = {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).casefold()]
    return int(number * scale)


def _find_author(heading, article_url: str) -> str | None:
    article_path_parts = urlsplit(article_url).path.strip("/").split("/")
    if not article_path_parts or not article_path_parts[0].startswith("@"):
        return None

    expected_profile_path = f"/{article_path_parts[0]}"
    for link in heading.find_all_previous("a", href=True):
        profile_url = urlsplit(link["href"])
        author = _normalized_text(link)
        if profile_url.path.rstrip("/") == expected_profile_path and author:
            return author
    return None


def _is_medium_article_url(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").casefold()
    path_parts = parts.path.strip("/").split("/")
    if host == "medium.com":
        return len(path_parts) >= 2
    if host.endswith(".medium.com") and host != "www.medium.com":
        return bool(path_parts and path_parts[0])
    return False


def _without_tracking(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _normalized_text(element) -> str:
    return " ".join(element.get_text(" ", strip=True).split())
