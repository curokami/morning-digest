from __future__ import annotations

import logging

import feedparser

from morning_digest.domain import Article


class MediumCollector:
    def __init__(self, logger=None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, feeds: list[str | dict]) -> list[Article]:
        articles: list[Article] = []
        for feed in feeds:
            feed_url, weight = self._feed_settings(feed)
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
                    preference_weight=weight,
                ))
        return list({article.canonical_url: article for article in articles}.values())

    @staticmethod
    def _feed_settings(feed: str | dict) -> tuple[str, float]:
        if isinstance(feed, str):
            return feed, 1.0
        if not isinstance(feed, dict) or not isinstance(feed.get("url"), str):
            raise ValueError("Each Medium feed must be a URL string or a mapping with a url")
        weight = float(feed.get("weight", 1.0))
        if weight <= 0:
            raise ValueError("Medium feed weight must be greater than zero")
        return feed["url"], weight
