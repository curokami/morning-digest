from __future__ import annotations


class CollectorGroup:
    """Present several independently configured collectors as one collector."""

    def __init__(self, sources: list[tuple[object, object]]) -> None:
        self.sources = sources

    def collect(self, _unused=None):
        collected = []
        for collector, settings in self.sources:
            collected.extend(collector.collect(settings))

        # Prefer the strongest preference when sources link to the same Article.
        by_url = {}
        for article in collected:
            existing = by_url.get(article.canonical_url)
            if existing is None or article.preference_weight > existing.preference_weight:
                by_url[article.canonical_url] = article
        return list(by_url.values())
