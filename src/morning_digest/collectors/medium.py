from __future__ import annotations

import logging

import feedparser

from morning_digest.domain import Article


class MediumCollector:
    def __init__(self, logger=None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, feeds: list[str]) -> list[Article]:
        articles: list[Article] = []
        for feed_url in feeds:
            parsed = feedparser.parse(feed_url)
            if getattr(parsed, "bozo", False) and not parsed.entries:
                self.logger.error("Could not read Medium feed: %s", feed_url)
                continue
            for entry in parsed.entries:
                url = entry.get("link")
                title = entry.get("title")
                if not url or not title:
                    continue
                tags = tuple(tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term"))
                articles.append(Article(
                    title=title.strip(), canonical_url=url.split("?")[0], source="Medium",
                    author=entry.get("author"), publication_date=entry.get("published"),
                    source_tags=tags,
                    content=entry.get("content", [{}])[0].get("value", ""),
                ))
        return list({article.canonical_url: article for article in articles}.values())
