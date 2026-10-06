from __future__ import annotations

import argparse
import logging
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from morning_digest.ai import OpenAIProcessor
from morning_digest.collectors import (
    ElixirLibHuntCollector,
    MediumCollector,
    MediumEmailCollector,
    PythonWeeklyCollector,
)
from morning_digest.collectors.gmail_inbox import GmailInboxReader
from morning_digest.config import load_config
from morning_digest.credentials import load_credentials
from morning_digest.delivery import GmailDelivery
from morning_digest.digest import HtmlDigestBuilder
from morning_digest.enrichment import ArticleEnricher, ExistingContentEnricher
from morning_digest.persistence import JsonStore
from morning_digest.pipeline import Pipeline
from morning_digest.scheduling import select_rotating_feeds, source_is_due
from morning_digest.taxonomy import Taxonomy


def build_medium_collection(
    medium: dict[str, Any],
    credentials: dict[str, str],
    today: date,
):
    """Build the configured Medium collector and the inputs it needs."""
    acquisition = str(medium.get("acquisition", "rss")).casefold()
    all_feeds = medium.get("feeds", [])
    tag_weight_rules = medium.get("tag_weight_rules", [])

    if acquisition == "rss":
        rotation_days = int(medium.get("polling", {}).get("rotation_days", 3))
        feeds = select_rotating_feeds(all_feeds, today, rotation_days)
        return MediumCollector(tag_weight_rules), feeds
    if acquisition == "email":
        reader = GmailInboxReader(
            credentials["GMAIL_USERNAME"], credentials["GMAIL_APP_PASSWORD"]
        )
        return MediumEmailCollector(reader, tag_weight_rules), all_feeds
    raise ValueError("Medium acquisition must be 'rss' or 'email'")


def build_medium_enricher(medium: dict[str, Any]):
    """Choose enrichment without bypassing the configured acquisition boundary."""
    acquisition = str(medium.get("acquisition", "rss")).casefold()
    if acquisition == "rss":
        return ArticleEnricher()
    if acquisition == "email":
        return ExistingContentEnricher()
    raise ValueError("Medium acquisition must be 'rss' or 'email'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and send the Morning Digest")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    log_config = config.section("logging")
    log_path = config.path(log_config.get("path", "logs/morning-digest.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=log_config.get("level", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")])
    taxonomy_config = config.section("taxonomy")
    taxonomy = Taxonomy.load(config.path(taxonomy_config["path"]))
    delivery_config = config.section("delivery")
    credentials = load_credentials(
        ("OPENAI_API_KEY", "GMAIL_USERNAME", "GMAIL_APP_PASSWORD", "GMAIL_RECIPIENT"))
    sources_config = config.section("sources")
    medium = sources_config.get("medium", {})
    app_config = config.section("app")
    now = datetime.now(ZoneInfo(app_config.get("timezone", "Asia/Tokyo")))
    python_weekly = sources_config.get("python_weekly", {})
    awesome_elixir = sources_config.get("awesome_elixir", {})
    processor = OpenAIProcessor(config.section("ai")["model"], taxonomy)
    store = JsonStore(config.path(config.section("persistence")["path"]))
    builder = HtmlDigestBuilder()
    delivery = GmailDelivery(credentials["GMAIL_USERNAME"], credentials["GMAIL_APP_PASSWORD"],
        credentials["GMAIL_RECIPIENT"],
        delivery_config.get("sender", {}).get("name", "Morning Digest"))
    default_subject = delivery_config.get("subject", {}).get("prefix", "Morning Digest")
    results = []

    if medium.get("enabled", True):
        digest = medium.get("digest", {})
        collector, feeds = build_medium_collection(medium, credentials, now.date())
        enricher = build_medium_enricher(medium)
        logging.getLogger(__name__).info(
            "Medium acquisition selected: mode=%s inputs=%d",
            medium.get("acquisition", "rss"), len(feeds))
        pipeline = Pipeline(collector, enricher, processor, store, builder, delivery)
        results.append(pipeline.run(
            feeds,
            int(digest.get("max_articles", app_config.get("max_articles_per_digest", 10))),
            digest.get("subject_prefix", default_subject),
            delivery_source="Medium",
        ))

    if python_weekly.get("enabled", False) and source_is_due(python_weekly.get("schedule"), now):
        digest = python_weekly.get("digest", {})
        pipeline = Pipeline(PythonWeeklyCollector(
            python_weekly.get("archive_url", "https://www.pythonweekly.com/archive"),
            sections=python_weekly.get("sections"),
            weight=float(python_weekly.get("weight", 1.0)),
        ), ArticleEnricher(), processor, store, builder, delivery)
        results.append(pipeline.run(
            [],
            int(digest.get("max_articles", 5)),
            digest.get("subject_prefix", "🐍 Python Weekly Digest"),
            delivery_source="Python Weekly",
        ))
    elif python_weekly.get("enabled", False):
        logging.getLogger(__name__).info("Python Weekly skipped: source is not due today")

    if awesome_elixir.get("enabled", False) and source_is_due(awesome_elixir.get("schedule"), now):
        digest = awesome_elixir.get("digest", {})
        pipeline = Pipeline(ElixirLibHuntCollector(
            awesome_elixir.get("feed_url", "https://elixir.libhunt.com/newsletter/feed")),
            ArticleEnricher(), processor, store, builder, delivery)
        results.append(pipeline.run(
            [], int(digest.get("max_articles", 5)),
            digest.get("subject_prefix", "⚗️ Awesome Elixir Digest"),
            delivery_source="Awesome Elixir",
        ))
    elif awesome_elixir.get("enabled", False):
        logging.getLogger(__name__).info("Awesome Elixir skipped: source is not due today")

    return 1 if any(result["delivery"] == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
