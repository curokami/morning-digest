import json
from types import SimpleNamespace

from morning_digest.ai import OpenAIProcessor
from morning_digest.collectors import MediumCollector
from morning_digest.domain import Article, ProcessingResult, ReadingPriority, Recommendation, Summary
from morning_digest.digest import HtmlDigestBuilder
from morning_digest.persistence import JsonStore
from morning_digest.taxonomy import Taxonomy


def result(url="https://example.com/a", priority=4):
    article = Article("A <title>", url, "Medium", source_tags=("python",), content="body")
    return ProcessingResult(article, "success", Summary("ja", "要約です。"),
        Recommendation(ReadingPriority(priority), "読む理由です。", ("Python",)))


def test_taxonomy_rejects_unknown_and_falls_back():
    taxonomy = Taxonomy({"Python", "Uncategorized"}, "Uncategorized")
    assert taxonomy.validate([]) == ("Uncategorized",)
    try:
        taxonomy.validate(["Invented"])
        assert False
    except ValueError:
        pass


def test_medium_feed_settings_support_weighted_and_legacy_forms():
    assert MediumCollector._feed_settings("https://medium.com/feed/@writer") == (
        "https://medium.com/feed/@writer", 1.0)
    assert MediumCollector._feed_settings({"url": "https://medium.com/feed/@favorite", "weight": 2}) == (
        "https://medium.com/feed/@favorite", 2.0)


def test_json_store_roundtrip_and_delivery_queue(tmp_path):
    store = JsonStore(tmp_path / "state.json")
    store.save_result(result())
    reopened = JsonStore(tmp_path / "state.json")
    assert reopened.is_successful("https://example.com/a")
    assert reopened.pending_results()[0].recommendation.reading_priority == ReadingPriority.HIGH
    reopened.mark_delivered(["https://example.com/a"])
    assert reopened.pending_results() == []


def test_html_is_sorted_and_escaped():
    digest = HtmlDigestBuilder().build([result(priority=2), result("https://example.com/b", 5)])
    assert digest.results[0].recommendation.reading_priority == 5
    assert "A &lt;title&gt;" in digest.html_content


def test_openai_schema_restricts_digest_tags_to_taxonomy():
    class Responses:
        def __init__(self):
            self.arguments = None

        def create(self, **kwargs):
            self.arguments = kwargs
            return SimpleNamespace(output_text=json.dumps({
                "summary": "要約です。", "reading_priority": 3,
                "reason_to_read": "読む理由です。", "digest_tags": ["Python"],
            }))

    responses = Responses()
    client = SimpleNamespace(responses=responses)
    taxonomy = Taxonomy({"Python", "Uncategorized"}, "Uncategorized")
    processor = OpenAIProcessor("test-model", taxonomy, client=client)
    processor.process(Article("title", "https://example.com", "Medium", content="body"))

    tag_schema = responses.arguments["text"]["format"]["schema"]["properties"]["digest_tags"]
    assert tag_schema["items"]["enum"] == ["Python", "Uncategorized"]
    assert tag_schema["maxItems"] == 3
    assert json.loads(responses.arguments["input"])["writer_preference_weight"] == 1.0
