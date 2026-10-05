from datetime import datetime, timezone

from morning_digest.collectors.medium_email import EmailBody, EmailMetadata, ParsedEmail
from morning_digest.collectors.medium_email_collector import MediumEmailCollector


class StubInboxReader:
    def __init__(self, digest: ParsedEmail | None) -> None:
        self.digest = digest
        self.read_count = 0

    def read_latest_medium_daily_digest(self) -> ParsedEmail | None:
        self.read_count += 1
        return self.digest


def test_collects_weighted_articles_from_latest_medium_digest_email():
    reader = StubInboxReader(ParsedEmail(
        metadata=EmailMetadata(
            subject="Today's Medium Daily Digest",
            sender="Medium Daily Digest <noreply@medium.com>",
            sent_at=datetime(2026, 10, 5, 7, 20, tzinfo=timezone.utc),
        ),
        body=EmailBody(
            content_type="text/html",
            content="""
            <a href="https://medium.com/@favorite">Favorite Writer</a>
            <a href="https://medium.com/@favorite/python-tools-123456789abc">
              <h2>Python Tools</h2><h3>Useful tools for developers.</h3>
            </a>
            """,
        ),
    ))
    collector = MediumEmailCollector(
        reader,
        text_weight_rules=[{"all": ["Python"], "weight": 2.0}],
    )

    articles = collector.collect([
        {"url": "https://medium.com/feed/@favorite", "weight": 2.0},
    ])

    assert reader.read_count == 1
    assert len(articles) == 1
    assert articles[0].title == "Python Tools"
    assert articles[0].preference_weight == 4.0


def test_collects_nothing_when_inbox_has_no_medium_digest():
    reader = StubInboxReader(None)
    collector = MediumEmailCollector(reader)

    assert collector.collect([]) == []
    assert reader.read_count == 1
