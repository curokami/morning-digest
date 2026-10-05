from __future__ import annotations

from morning_digest.collectors.medium_digest_html import extract_articles
from morning_digest.collectors.medium_email import ParsedEmail
from morning_digest.domain import Article


def articles_from_medium_digest(digest: ParsedEmail) -> list[Article]:
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
        )
        for candidate in extract_articles(digest.body.content)
    ]
