from __future__ import annotations

import logging

import feedparser

from morning_digest.domain import Article


class MediumCollector:
    def __init__(self, tag_weight_rules: list[dict] | None = None, logger=None) -> None:
        self.tag_weight_rules = self._validate_tag_weight_rules(tag_weight_rules or [])
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
                    content=self._entry_content(entry),
                    preference_weight=weight * self._tag_weight(tags),
                ))
        return list({article.canonical_url: article for article in articles}.values())

    @staticmethod
    def _entry_content(entry) -> str:
        """Return the richest body supplied by RSS without assuming one feed shape."""
        candidates = [
            item.get("value", "")
            for item in entry.get("content", [])
            if isinstance(item, dict)
        ]
        candidates.extend((entry.get("summary", ""), entry.get("description", "")))
        return max((value for value in candidates if isinstance(value, str)),
                   key=len, default="")

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

    @staticmethod
    def _validate_tag_weight_rules(rules: list[dict]) -> tuple[tuple[frozenset[str], float], ...]:
        validated: list[tuple[frozenset[str], float]] = []
        for rule in rules:
            if not isinstance(rule, dict) or not isinstance(rule.get("all"), list):
                raise ValueError("Each tag weight rule must contain an all list")
            required = frozenset(
                str(tag).strip().casefold() for tag in rule["all"] if str(tag).strip()
            )
            weight = float(rule.get("weight", 1.0))
            if not required or weight <= 0:
                raise ValueError("Tag weight rules require tags and a positive weight")
            validated.append((required, weight))
        return tuple(validated)

    def _tag_weight(self, tags: tuple[str, ...]) -> float:
        normalized = {tag.strip().casefold() for tag in tags}
        multiplier = 1.0
        for required, weight in self.tag_weight_rules:
            if required <= normalized:
                multiplier *= weight
        return multiplier
