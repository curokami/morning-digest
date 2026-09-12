from morning_digest.domain import Article, DeliveryResult, ProcessingResult, ReadingPriority, Recommendation, Summary
from morning_digest.digest import HtmlDigestBuilder
from morning_digest.enrichment import ArticleAccessError
from morning_digest.persistence import JsonStore
from morning_digest.pipeline import Pipeline


class Collector:
    def collect(self, feeds):
        return [Article("ok", "https://e/ok", "Medium"), Article("bad", "https://e/bad", "Medium")]

class Enricher:
    def enrich(self, article): return article

class Processor:
    def process(self, article):
        if article.title == "bad": raise RuntimeError("boom")
        return ProcessingResult(article, "success", Summary("ja", "要約"),
            Recommendation(ReadingPriority.WORTH_READING, "理由", ("Python",)))

class Delivery:
    def __init__(self, statuses=None):
        self.calls = 0
        self.statuses = list(statuses or ["success"])
    def send(self, digest, subject_prefix):
        self.calls += 1
        status = self.statuses.pop(0) if self.statuses else "success"
        return DeliveryResult(status, error="temporary" if status == "failed" else None)

def test_pipeline_isolates_failure_and_deduplicates(tmp_path):
    delivery = Delivery()
    pipeline = Pipeline(Collector(), Enricher(), Processor(), JsonStore(tmp_path / "state.json"), HtmlDigestBuilder(), delivery)
    first = pipeline.run(["feed"])
    second = pipeline.run(["feed"])
    assert first == {"candidates": 2, "succeeded": 1, "delivery": "success"}
    assert second["candidates"] == 1
    assert delivery.calls == 1


def test_delivery_retry_reuses_persisted_ai_result(tmp_path):
    delivery = Delivery(["failed", "success"])
    store = JsonStore(tmp_path / "state.json")
    pipeline = Pipeline(Collector(), Enricher(), Processor(), store, HtmlDigestBuilder(), delivery)
    first = pipeline.run(["feed"])
    assert first["delivery"] == "failed"
    assert len(store.pending_results()) == 1
    second = pipeline.run(["feed"])
    assert second["succeeded"] == 0
    assert second["delivery"] == "success"
    assert delivery.calls == 2
    assert store.pending_results() == []


def test_pipeline_selects_higher_weight_before_article_limit(tmp_path):
    class WeightedCollector:
        def collect(self, feeds):
            return [
                Article("normal", "https://e/normal", "Medium", preference_weight=1.0),
                Article("favorite", "https://e/favorite", "Medium", preference_weight=2.0),
            ]

    class TrackingProcessor(Processor):
        def __init__(self): self.titles = []

        def process(self, article):
            self.titles.append(article.title)
            return super().process(article)

    processor = TrackingProcessor()
    pipeline = Pipeline(WeightedCollector(), Enricher(), processor,
        JsonStore(tmp_path / "state.json"), HtmlDigestBuilder(), Delivery())
    pipeline.run(["feed"], max_articles=1)
    assert processor.titles == ["favorite"]


def test_separate_source_runs_send_separate_digests(tmp_path):
    class SourceCollector:
        def __init__(self, source): self.source = source
        def collect(self, feeds):
            return [Article(self.source, f"https://e/{self.source}", self.source)]

    class CapturingDelivery(Delivery):
        def __init__(self):
            super().__init__()
            self.subjects = []
            self.sources = []
            self.html_messages = []

        def send(self, digest, subject_prefix):
            self.subjects.append(subject_prefix)
            self.sources.append({result.article.source for result in digest.results})
            self.html_messages.append(digest.html_content)
            return super().send(digest, subject_prefix)

    store = JsonStore(tmp_path / "state.json")
    delivery = CapturingDelivery()
    for source, subject in (("Medium", "Morning Digest"),
                            ("Python Weekly", "🐍 Python Weekly Digest")):
        pipeline = Pipeline(SourceCollector(source), Enricher(), Processor(), store,
                            HtmlDigestBuilder(), delivery)
        pipeline.run([], subject_prefix=subject, delivery_source=source)

    assert delivery.subjects == ["Morning Digest", "🐍 Python Weekly Digest"]
    assert "<h1>🐍 Python Weekly Digest</h1>" in delivery.html_messages[1]
    assert delivery.sources == [{"Medium"}, {"Python Weekly"}]


def test_access_denial_is_retried_three_times_then_reported_and_excluded(tmp_path):
    class OneArticleCollector:
        def collect(self, feeds):
            return [Article("blocked", "https://e/blocked", "Medium")]

    class BlockedEnricher:
        def enrich(self, article):
            raise ArticleAccessError(
                "denied", "bot_protection_suspected", 403, ("body:captcha",))

    store = JsonStore(tmp_path / "state.json")
    delivery = Delivery()
    pipeline = Pipeline(OneArticleCollector(), BlockedEnricher(), Processor(), store,
                        HtmlDigestBuilder(), delivery)

    assert pipeline.run(["feed"])["delivery"] == "skipped"
    assert pipeline.run(["feed"])["delivery"] == "skipped"
    assert pipeline.run(["feed"])["delivery"] == "success"
    assert delivery.calls == 1
    assert store.data["articles"]["https://e/blocked"]["status"] == "retrieval_exhausted"
    assert store.data["articles"]["https://e/blocked"]["attempt_count"] == 3
    assert pipeline.run(["feed"])["candidates"] == 0
    assert delivery.calls == 1
