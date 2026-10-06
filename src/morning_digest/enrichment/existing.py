from morning_digest.domain import Article


class ExistingContentEnricher:
    """Keep content supplied by a trusted source without fetching its URL."""

    def enrich(self, article: Article) -> Article:
        return article
