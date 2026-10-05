from datetime import datetime, timezone

from morning_digest.collectors.medium_email import EmailBody, EmailMetadata, ParsedEmail
from morning_digest.collectors.medium_email_articles import articles_from_medium_digest
from morning_digest.domain import Article


def test_converts_medium_digest_email_to_articles():
    digest = ParsedEmail(
        metadata=EmailMetadata(
            subject="Today's Medium Daily Digest",
            sender="Medium Daily Digest <noreply@medium.com>",
            sent_at=datetime(2026, 10, 5, 7, 20, tzinfo=timezone.utc),
        ),
        body=EmailBody(
            content_type="text/html",
            content="""
            <a href="https://medium.com/@alice">Alice Example</a>
            <a href="https://medium.com/@alice/useful-python-123456789abc?source=email">
              <h2>Useful Python</h2><h3>A practical Python article.</h3>
            </a>
            <a href="https://medium.com/@bob">Bob Example</a>
            <a href="https://medium.com/@bob/elixir-patterns-abcdef123456?source=email">
              <h2>Elixir Patterns</h2><h3>A practical Elixir article.</h3>
            </a>
            """,
        ),
    )

    articles = articles_from_medium_digest(digest)

    assert articles == [
        Article(
            title="Useful Python",
            canonical_url="https://medium.com/@alice/useful-python-123456789abc",
            source="Medium",
            author="Alice Example",
            publication_date="2026-10-05T07:20:00+00:00",
            content="A practical Python article.",
        ),
        Article(
            title="Elixir Patterns",
            canonical_url="https://medium.com/@bob/elixir-patterns-abcdef123456",
            source="Medium",
            author="Bob Example",
            publication_date="2026-10-05T07:20:00+00:00",
            content="A practical Elixir article.",
        ),
    ]


def test_rejects_plain_text_digest_body():
    digest = ParsedEmail(
        metadata=EmailMetadata(
            subject="Today's Medium Daily Digest",
            sender="Medium Daily Digest <noreply@medium.com>",
            sent_at=datetime(2026, 10, 5, 7, 20, tzinfo=timezone.utc),
        ),
        body=EmailBody(content_type="text/plain", content="No HTML body"),
    )

    try:
        articles_from_medium_digest(digest)
    except ValueError as error:
        assert str(error) == "Medium Daily Digest requires an HTML body"
    else:
        raise AssertionError("Expected a non-HTML digest body to be rejected")
