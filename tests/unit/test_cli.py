from datetime import date

from morning_digest.cli import build_medium_collection, build_medium_enricher
from morning_digest.collectors import MediumCollector, MediumEmailCollector
from morning_digest.enrichment import ArticleEnricher, ExistingContentEnricher


def test_builds_rss_collection_by_default_with_rotated_feeds():
    medium = {
        "polling": {"rotation_days": 2},
        "feeds": [
            "https://medium.com/feed/@one",
            "https://medium.com/feed/@two",
            {"url": "https://medium.com/feed/@favorite", "weight": 2.0},
        ],
    }

    collector, feeds = build_medium_collection(medium, {}, date(2026, 10, 5))

    assert isinstance(collector, MediumCollector)
    assert len(feeds) == 2
    assert medium["feeds"][2] in feeds


def test_builds_email_collection_with_all_feeds_for_author_weights():
    medium = {
        "acquisition": "email",
        "tag_weight_rules": [{"all": ["Python"], "weight": 2.0}],
        "feeds": [
            "https://medium.com/feed/@one",
            {"url": "https://medium.com/feed/@favorite", "weight": 2.0},
        ],
    }
    credentials = {
        "GMAIL_USERNAME": "reader@example.com",
        "GMAIL_APP_PASSWORD": "app-password",
    }

    collector, feeds = build_medium_collection(
        medium, credentials, date(2026, 10, 5)
    )

    assert isinstance(collector, MediumEmailCollector)
    assert feeds == medium["feeds"]
    assert collector.inbox_reader.username == "reader@example.com"
    assert collector.text_weight_rules == medium["tag_weight_rules"]


def test_rejects_unknown_medium_acquisition_mode():
    try:
        build_medium_collection({"acquisition": "unknown"}, {}, date(2026, 10, 5))
    except ValueError as error:
        assert str(error) == "Medium acquisition must be 'rss' or 'email'"
    else:
        raise AssertionError("Expected an unknown acquisition mode to be rejected")


def test_uses_existing_email_content_without_web_enrichment():
    assert isinstance(
        build_medium_enricher({"acquisition": "email"}),
        ExistingContentEnricher,
    )


def test_keeps_web_enrichment_for_rss_mode():
    assert isinstance(build_medium_enricher({}), ArticleEnricher)
