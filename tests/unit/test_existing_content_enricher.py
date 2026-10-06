from unittest.mock import patch

from morning_digest.domain import Article
from morning_digest.enrichment import ExistingContentEnricher


def test_returns_email_article_without_requesting_its_url():
    article = Article(
        title="An article selected by Medium",
        canonical_url="https://medium.com/@writer/an-article-123456789abc",
        source="Medium",
        content="The short summary supplied in the Medium Daily Digest.",
    )

    with patch("morning_digest.enrichment.web.urlopen") as urlopen:
        enriched = ExistingContentEnricher().enrich(article)

    urlopen.assert_not_called()
    assert enriched == article
