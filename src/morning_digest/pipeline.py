from __future__ import annotations

import logging

from morning_digest.domain import ProcessingResult
from morning_digest.enrichment import ArticleAccessError


class Pipeline:
    def __init__(self, collector, enricher, processor, store, builder, delivery, logger=None) -> None:
        self.collector, self.enricher, self.processor = collector, enricher, processor
        self.store, self.builder, self.delivery = store, builder, delivery
        self.logger = logger or logging.getLogger(__name__)

    def run(self, feeds: list[str | dict], max_articles: int = 10,
            subject_prefix: str = "Morning Digest", delivery_source: str | None = None) -> dict:
        self.logger.info("Digest run started: source=%s", delivery_source or "all")
        candidates = [a for a in self.collector.collect(feeds) if self.store.should_process(a.canonical_url)]
        articles = sorted(candidates, key=lambda article: article.preference_weight, reverse=True)[:max_articles]
        succeeded = 0
        for article in articles:
            try:
                result = self.processor.process(self.enricher.enrich(article))
                self.store.save_result(result)
                succeeded += 1
            except Exception as exc:
                self.logger.exception("Article failed: %s", article.canonical_url)
                if isinstance(exc, ArticleAccessError):
                    attempts = self.store.failure_attempt_count(article.canonical_url) + 1
                    status = "retrieval_exhausted" if attempts >= 3 else "retry_pending"
                    self.store.save_result(ProcessingResult(
                        article=article, status=status, error=str(exc),
                        error_classification=exc.classification, attempt_count=attempts))
                else:
                    self.store.save_result(ProcessingResult(article=article, status="failed", error=str(exc)))
        pending = self.store.pending_results(delivery_source)
        failed = self.store.pending_failure_results(delivery_source)
        delivery_status = "skipped"
        if pending or failed:
            digest = self.builder.build(pending, failed_results=failed, title=subject_prefix)
            delivery = self.delivery.send(digest, subject_prefix)
            delivery_status = delivery.status
            if delivery.status == "success":
                self.store.mark_delivered([r.article.canonical_url for r in pending + failed])
            else:
                self.logger.error("Delivery failed: %s", delivery.error)
        self.logger.info("Run finished: source=%s collected=%d succeeded=%d delivery=%s",
                         delivery_source or "all", len(articles), succeeded, delivery_status)
        return {"candidates": len(articles), "succeeded": succeeded, "delivery": delivery_status}
