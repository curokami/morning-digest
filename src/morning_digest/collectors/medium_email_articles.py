from __future__ import annotations

from collections.abc import Iterable, Mapping
from urllib.parse import urlsplit

from morning_digest.collectors.medium_digest_html import extract_articles
from morning_digest.collectors.medium_email import ParsedEmail
from morning_digest.domain import Article


def medium_author_weights(feeds: Iterable[str | dict]) -> dict[str, float]:
    """Build author weights from existing Medium author-feed settings."""
    weights: dict[str, float] = {}
    for feed in feeds:
        feed_url = feed if isinstance(feed, str) else feed.get("url")
        if not isinstance(feed_url, str):
            continue
        path_parts = urlsplit(feed_url).path.strip("/").split("/")
        if len(path_parts) < 2 or path_parts[0] != "feed" or not path_parts[1].startswith("@"):
            continue
        weight = float(feed.get("weight", 1.0)) if isinstance(feed, dict) else 1.0
        if weight <= 0:
            raise ValueError("Medium author weight must be greater than zero")
        weights[path_parts[1].casefold()] = weight
    return weights


def articles_from_medium_digest(
    digest: ParsedEmail,
    author_weights: Mapping[str, float] | None = None,
) -> list[Article]:
    """Convert a parsed Medium Daily Digest email into domain articles."""
    if digest.body.content_type != "text/html":
        raise ValueError("Medium Daily Digest requires an HTML body")

    publication_date = digest.metadata.sent_at.isoformat()
    return [
        Article(
            title=candidate.title,
            canonical_url=candidate.canonical_url,
            source="Medium",
            author=candidate.author,
            publication_date=publication_date,
            content=candidate.summary,
            preference_weight=_article_author_weight(
                candidate.canonical_url, author_weights or {}
            ),
        )
        for candidate in extract_articles(digest.body.content)
    ]


def _article_author_weight(article_url: str, author_weights: Mapping[str, float]) -> float:
    author_id = _medium_author_id(article_url)
    return author_weights.get(author_id, 1.0) if author_id else 1.0


def _medium_author_id(article_url: str) -> str | None:
    parts = urlsplit(article_url)
    host = (parts.hostname or "").casefold()
    path_parts = parts.path.strip("/").split("/")
    if host == "medium.com" and path_parts and path_parts[0].startswith("@"):
        return path_parts[0].casefold()
    if host.endswith(".medium.com"):
        subdomain = host.removesuffix(".medium.com")
        if subdomain and subdomain != "www":
            return f"@{subdomain}"
    return None
