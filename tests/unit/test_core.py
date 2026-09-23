import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from morning_digest.ai import OpenAIProcessor
from morning_digest.collectors import (
    CollectorGroup, ElixirLibHuntCollector, MediumCollector, PythonWeeklyCollector,
)
from morning_digest.domain import Article, ProcessingResult, ReadingPriority, Recommendation, Summary
from morning_digest.delivery import GmailDelivery
from morning_digest.digest import HtmlDigestBuilder
from morning_digest.enrichment import ArticleEnricher
from morning_digest.persistence import JsonStore
from morning_digest.scheduling import select_rotating_feeds, source_is_due
from morning_digest.taxonomy import Taxonomy
from morning_digest.window_launcher import choose_delay, is_stale_run


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
        "https://medium.com/feed/@writer", 1.0, None)
    assert MediumCollector._feed_settings({"url": "https://medium.com/feed/@favorite", "weight": 2}) == (
        "https://medium.com/feed/@favorite", 2.0, None)
    assert MediumCollector._feed_settings({"url": "https://medium.com/feed/tag/omarchy", "limit": 2}) == (
        "https://medium.com/feed/tag/omarchy", 1.0, 2)


def test_medium_feed_content_uses_richest_available_rss_body():
    entry = {
        "content": [{"value": "short"}],
        "summary": "summary body is longer",
        "description": "description",
    }
    assert MediumCollector._entry_content(entry) == "summary body is longer"


def test_medium_feed_limit_bounds_entries_before_article_creation():
    entries = [
        {"title": f"Story {number}", "link": f"https://example.com/{number}"}
        for number in range(3)
    ]
    parsed = SimpleNamespace(bozo=False, entries=entries)

    with patch("morning_digest.collectors.medium.feedparser.parse", return_value=parsed):
        articles = MediumCollector().collect([
            {"url": "https://medium.com/feed/tag/omarchy", "limit": 2}
        ])

    assert [article.title for article in articles] == ["Story 0", "Story 1"]


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


def test_elixir_libhunt_extracts_editorial_entries_and_excludes_sponsors():
    issue = '''
      <h3 class="section-title">Popular News and Articles</h3>
      <ul>
        <li><a class="title" href="https://video.example/hologram">Hologram: Local First</a></li>
        <li><a class="title" href="https://forum.example/hologram">Hologram: Local First (Talk)</a>
          <p class="description">A substantially richer explanation of local-first synchronization.</p></li>
        <li id="sponsored"><a class="title" href="https://ads.example">Advertisement</a></li>
      </ul>
      <h3 class="section-title">Trending packages and projects</h3>
      <ul>
        <li><a href="https://github.com/example/popcorn">GitHub</a>
          <a class="title" href="https://libhunt.example/popcorn">popcorn</a>
          <p class="description">Running Elixir in the browser</p></li>
      </ul>
    '''
    feed = SimpleNamespace(entries=[{
        "link": "https://elixir.libhunt.com/newsletter/538",
        "published": "2026-09-17",
    }])
    collector = ElixirLibHuntCollector(
        "https://elixir.libhunt.com/newsletter/feed",
        fetcher=lambda _url: issue,
        feed_parser=lambda _url: feed,
    )

    articles = collector.collect([])

    assert [article.title for article in articles] == ["Hologram: Local First (Talk)", "popcorn"]
    assert articles[0].canonical_url == "https://forum.example/hologram"
    assert articles[0].preference_weight == 2.0
    assert articles[1].canonical_url == "https://github.com/example/popcorn"
    assert all(article.source == "Awesome Elixir" for article in articles)


def test_weekly_source_is_due_only_on_configured_weekday():
    schedule = {"frequency": "weekly", "weekday": "friday"}
    assert source_is_due(schedule, datetime(2026, 9, 11))
    assert not source_is_due(schedule, datetime(2026, 9, 10))


def test_medium_feeds_rotate_ordinary_sources_but_keep_preferred_daily():
    ordinary = [f"https://medium.com/feed/@writer{index}" for index in range(7)]
    favorite = {"url": "https://medium.com/feed/@favorite", "weight": 2.0}
    tag = {"url": "https://medium.com/feed/tag/omarchy", "daily": True}
    feeds = ordinary + [favorite, tag]

    selections = [
        select_rotating_feeds(feeds, datetime(2026, 9, day).date(), 3)
        for day in (18, 19, 20)
    ]

    assert all(favorite in selection and tag in selection for selection in selections)
    selected_ordinary = [
        feed for selection in selections for feed in selection if isinstance(feed, str)
    ]
    assert sorted(selected_ordinary) == sorted(ordinary)
    assert len(selected_ordinary) == len(set(selected_ordinary))


def test_random_window_delay_stays_between_0800_and_1050():
    assert choose_delay(datetime(2026, 9, 17, 8, 0), lambda upper: upper - 1) == 10_200
    assert choose_delay(datetime(2026, 9, 17, 9, 30), lambda upper: upper - 1) == 4_800
    assert choose_delay(datetime(2026, 9, 17, 10, 51), lambda upper: 0) is None


def test_random_window_runs_late_same_day_but_rejects_stale_next_day():
    started = datetime(2026, 9, 23, 8, 0)
    assert not is_stale_run(started, datetime(2026, 9, 23, 11, 50))
    assert is_stale_run(started, datetime(2026, 9, 24, 7, 0))


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


def test_html_uses_source_specific_title():
    digest = HtmlDigestBuilder().build([result()], title="🐍 Python Weekly Digest")
    assert "🐍 Python Weekly Digest</h1>" in digest.html_content
    assert "今週の一押し" in digest.html_content
    assert "#285c47" in digest.html_content


def test_html_adds_hot_coffee_to_daily_digest_title():
    digest = HtmlDigestBuilder().build([result()], title="Morning Digest")
    assert 'src="cid:morning-digest-coffee"' in digest.html_content
    assert "Morning Digest</h1>" in digest.html_content
    assert "A <title>" in digest.plain_content
    assert "https://example.com/a" in digest.plain_content
    assert "要約です。" in digest.plain_content
    assert "読む理由: 読む理由です。" in digest.plain_content


def test_html_uses_elixir_weekly_identity_without_coffee_image():
    elixir_result = result()
    elixir_result = ProcessingResult(
        Article("Elixir article", "https://example.com/elixir", "Awesome Elixir"),
        elixir_result.status, elixir_result.summary, elixir_result.recommendation)
    digest = HtmlDigestBuilder().build([elixir_result], title="⚗️ Awesome Elixir Digest")
    assert "⚗️ Awesome Elixir Digest</h1>" in digest.html_content
    assert "今週の一押し" in digest.html_content
    assert "#60417a" in digest.html_content
    assert "cid:morning-digest-coffee" not in digest.html_content


def test_gmail_message_uses_related_root_with_alternative_and_inline_image():
    digest = HtmlDigestBuilder().build([result()], title="Morning Digest")
    message = GmailDelivery("from@example.com", "password", "to@example.com")._build_message(
        digest, "Morning Digest")

    assert message.get_content_type() == "multipart/related"
    root_parts = list(message.iter_parts())
    assert [part.get_content_type() for part in root_parts] == [
        "multipart/alternative", "image/jpeg"]

    alternative, image = root_parts
    alternatives = list(alternative.iter_parts())
    assert [part.get_content_type() for part in alternatives] == ["text/plain", "text/html"]
    assert "要約です。" in alternatives[0].get_content()
    assert "cid:morning-digest-coffee" in alternatives[1].get_content()
    assert image["Content-ID"] == "<morning-digest-coffee>"
    assert image.get_content_disposition() == "inline"


def test_gmail_message_without_inline_image_has_alternative_root():
    digest = HtmlDigestBuilder().build([result()], title="🐍 Python Weekly Digest")
    message = GmailDelivery("from@example.com", "password", "to@example.com")._build_message(
        digest, "🐍 Python Weekly Digest")

    assert message.get_content_type() == "multipart/alternative"
    assert [part.get_content_type() for part in message.iter_parts()] == [
        "text/plain", "text/html"]


def test_html_features_only_first_article_with_quiet_priority_labels():
    digest = HtmlDigestBuilder().build([result(priority=2), result("https://example.com/b", 5)])
    assert digest.html_content.count("今日の一押し") == 1
    assert "まず読みたい" in digest.html_content
    assert "気になったら" in digest.html_content
    assert "Priority 5" not in digest.html_content
    assert "#526b7b" in digest.html_content


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
