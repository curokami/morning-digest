from __future__ import annotations

import argparse
import logging

from morning_digest.ai import OpenAIProcessor
from morning_digest.collectors import MediumCollector
from morning_digest.config import load_config
from morning_digest.credentials import load_credentials
from morning_digest.delivery import GmailDelivery
from morning_digest.digest import HtmlDigestBuilder
from morning_digest.enrichment import ArticleEnricher
from morning_digest.persistence import JsonStore
from morning_digest.pipeline import Pipeline
from morning_digest.taxonomy import Taxonomy


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and send the Morning Digest")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
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
    source = config.section("sources").get("medium", {})
    pipeline = Pipeline(MediumCollector(source.get("tag_weight_rules", [])), ArticleEnricher(),
        OpenAIProcessor(config.section("ai")["model"], taxonomy),
        JsonStore(config.path(config.section("persistence")["path"])), HtmlDigestBuilder(),
        GmailDelivery(credentials["GMAIL_USERNAME"], credentials["GMAIL_APP_PASSWORD"],
            credentials["GMAIL_RECIPIENT"],
            delivery_config.get("sender", {}).get("name", "Morning Digest")))
    result = pipeline.run(source.get("feeds", []), config.section("app").get("max_articles_per_digest", 10),
        delivery_config.get("subject", {}).get("prefix", "Morning Digest"))
    return 1 if result["delivery"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
