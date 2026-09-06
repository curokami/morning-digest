from __future__ import annotations

import logging

from morning_digest.domain import ProcessingResult


class Pipeline:
    def __init__(self, collector, enricher, processor, store, builder, delivery, logger=None) -> None:
        self.collector, self.enricher, self.processor = collector, enricher, processor
        self.store, self.builder, self.delivery = store, builder, delivery
        self.logger = logger or logging.getLogger(__name__)

    def run(self, feeds: list[str], max_articles: int = 10, subject_prefix: str = "Morning Digest") -> dict:
        self.logger.info("Morning Digest run started")
        articles = [a for a in self.collector.collect(feeds) if not self.store.is_successful(a.canonical_url)][:max_articles]
        succeeded = 0
        for article in articles:
            try:
                result = self.processor.process(self.enricher.enrich(article))
                self.store.save_result(result)
                succeeded += 1
            except Exception as exc:
                self.logger.exception("Article failed: %s", article.canonical_url)
                self.store.save_result(ProcessingResult(article=article, status="failed", error=str(exc)))
        pending = self.store.pending_results()
        delivery_status = "skipped"
        if pending:
            digest = self.builder.build(pending)
            delivery = self.delivery.send(digest, subject_prefix)
            delivery_status = delivery.status
            if delivery.status == "success":
                self.store.mark_delivered([r.article.canonical_url for r in pending])
            else:
                self.logger.error("Delivery failed: %s", delivery.error)
        self.logger.info("Run finished: collected=%d succeeded=%d delivery=%s", len(articles), succeeded, delivery_status)
        return {"candidates": len(articles), "succeeded": succeeded, "delivery": delivery_status}
