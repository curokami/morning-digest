from __future__ import annotations

from morning_digest.collectors.medium_email_articles import (
    articles_from_medium_digest,
    medium_author_weights,
)
from morning_digest.domain import Article


class MediumEmailCollector:
    """Collect Medium articles from the latest Daily Digest in an inbox."""

    def __init__(self, inbox_reader, text_weight_rules: list[dict] | None = None) -> None:
        self.inbox_reader = inbox_reader
        self.text_weight_rules = text_weight_rules or []

    def collect(self, feeds: list[str | dict]) -> list[Article]:
        digest = self.inbox_reader.read_latest_medium_daily_digest()
        if digest is None:
            return []

        return articles_from_medium_digest(
            digest,
            author_weights=medium_author_weights(feeds),
            text_weight_rules=self.text_weight_rules,
        )
