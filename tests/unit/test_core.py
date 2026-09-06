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
