import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from morning_digest.ai import OpenAIProcessor
from morning_digest.collectors import CollectorGroup, MediumCollector, PythonWeeklyCollector
from morning_digest.domain import Article, ProcessingResult, ReadingPriority, Recommendation, Summary
from morning_digest.digest import HtmlDigestBuilder
from morning_digest.enrichment import ArticleEnricher
from morning_digest.persistence import JsonStore
from morning_digest.scheduling import source_is_due
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


def test_medium_feed_content_uses_richest_available_rss_body():
    entry = {
        "content": [{"value": "short"}],
        "summary": "summary body is longer",
        "description": "description",
    }
    assert MediumCollector._entry_content(entry) == "summary body is longer"


def test_medium_tag_weight_requires_all_tags_and_ignores_case():
    collector = MediumCollector([{"all": ["Elixir", "Programming"], "weight": 2.0}])
    assert collector._tag_weight(("elixir", "PROGRAMMING", "Technology")) == 2.0
    assert collector._tag_weight(("Elixir",)) == 1.0


def test_python_weekly_discovers_latest_issue_and_extracts_article_sections():
    archive = '''
      <a href="/p/python-weekly-issue-762-september-10-2026">Issue 762</a>
      <a href="/p/python-weekly-issue-761-september-3-2026">Issue 761</a>
    '''
    issue = '''
      <meta property="article:published_time" content="2026-09-10T12:00:00Z">
      <h5>Articles, Tutorials and Talks</h5>
      <div><h6><a href="https://example.com/article?utm_source=weekly&amp;page=2">Useful article</a></h6>
      <p>A useful article description with enough context.</p></div>
      <h5>Interesting Projects, Tools, and Libraries</h5>
      <div><h6><a href="https://github.com/example/project">Project</a></h6></div>
    '''
    pages = {
        "https://www.pythonweekly.com/archive": archive,
        "https://www.pythonweekly.com/p/python-weekly-issue-762-september-10-2026": issue,
    }
    collector = PythonWeeklyCollector(
        "https://www.pythonweekly.com/archive", fetcher=pages.__getitem__)
    articles = collector.collect()

    assert len(articles) == 1
    assert articles[0].title == "Useful article"
    assert articles[0].canonical_url == "https://example.com/article?page=2"
    assert articles[0].source == "Python Weekly"
    assert articles[0].source_tags == ("Python", "Articles, Tutorials and Talks")
    assert articles[0].publication_date == "2026-09-10T12:00:00Z"


def test_weekly_source_is_due_only_on_configured_weekday():
    schedule = {"frequency": "weekly", "weekday": "friday"}
    assert source_is_due(schedule, datetime(2026, 9, 11))
    assert not source_is_due(schedule, datetime(2026, 9, 10))


def test_collector_group_combines_sources_and_keeps_stronger_duplicate():
    class StaticCollector:
        def __init__(self, articles): self.articles = articles
        def collect(self, settings): return self.articles

    weak = Article("weak", "https://example.com/a", "one", preference_weight=1.0)
    strong = Article("strong", "https://example.com/a", "two", preference_weight=2.0)
    group = CollectorGroup([(StaticCollector([weak]), None), (StaticCollector([strong]), None)])
    assert group.collect()[0] == strong


def test_enricher_uses_meaningful_rss_content_without_web_request():
    rss_html = "<p>" + ("RSSから取得した本文です。" * 25) + "</p>"
    article = Article("title", "https://example.com/article", "Medium", content=rss_html)
    with patch("morning_digest.enrichment.web.urlopen") as urlopen:
        enriched = ArticleEnricher().enrich(article)
    urlopen.assert_not_called()
    assert "<p>" not in enriched.content
    assert len(enriched.content) >= ArticleEnricher.MINIMUM_CONTENT_LENGTH


def test_denial_classification_requires_challenge_evidence_for_bot_suspicion():
    classification, evidence = ArticleEnricher.classify_denial(
        403, {"Server": "cloudflare", "CF-Ray": "abc"},
        "Complete this captcha on the challenge-platform",
    )
    assert classification == "bot_protection_suspected"
    assert "body:captcha" in evidence

    classification, evidence = ArticleEnricher.classify_denial(
        403, {"Server": "cloudflare", "CF-Ray": "abc"}, "Forbidden",
    )
    assert classification == "forbidden_unknown"
    assert evidence == ("server:cloudflare", "header:cf-ray")


def test_denial_classification_identifies_authentication_signal():
    classification, _ = ArticleEnricher.classify_denial(
        403, {"Server": "cloudflare"}, "This is a member-only story. Sign in to continue.",
    )
    assert classification == "authentication_required"


def test_json_store_roundtrip_and_delivery_queue(tmp_path):
    store = JsonStore(tmp_path / "state.json")
    store.save_result(result())
    reopened = JsonStore(tmp_path / "state.json")
    assert reopened.is_successful("https://example.com/a")
    assert reopened.pending_results()[0].recommendation.reading_priority == ReadingPriority.HIGH
    reopened.mark_delivered(["https://example.com/a"])
    assert reopened.pending_results() == []


def test_json_store_filters_pending_delivery_by_source(tmp_path):
    store = JsonStore(tmp_path / "state.json")
    medium = result("https://example.com/medium")
    weekly = ProcessingResult(
        Article("Weekly", "https://example.com/weekly", "Python Weekly", content="body"),
        "success", Summary("ja", "要約です。"),
        Recommendation(ReadingPriority.HIGH, "理由です。", ("Python",)),
    )
    store.save_result(medium)
    store.save_result(weekly)
    assert [item.article.canonical_url for item in store.pending_results("Medium")] == [
        "https://example.com/medium"]
    assert [item.article.canonical_url for item in store.pending_results("Python Weekly")] == [
        "https://example.com/weekly"]


def test_html_is_sorted_and_escaped():
    digest = HtmlDigestBuilder().build([result(priority=2), result("https://example.com/b", 5)])
    assert digest.results[0].recommendation.reading_priority == 5
    assert "A &lt;title&gt;" in digest.html_content


def test_html_renders_adopted_failure_labels():
    failures = [ProcessingResult(
        Article(f"blocked-{classification}", f"https://example.com/{index}", "Medium"),
        "retrieval_exhausted", error_classification=classification, attempt_count=3,
    ) for index, classification in enumerate((
        "bot_protection_suspected", "authentication_required", "forbidden_unknown"))]
    html = HtmlDigestBuilder().build([], failed_results=failures).html_content
    assert "取得できなかった記事" in html
    assert "取得不能（ボット判定の疑い）" in html
    assert "取得不能（認証が必要な可能性）" in html
    assert "取得不能（原因不明のアクセス拒否）" in html


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
    assert json.loads(responses.arguments["input"])["preference_weight"] == 1.0
