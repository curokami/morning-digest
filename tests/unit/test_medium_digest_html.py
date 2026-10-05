from morning_digest.collectors.medium_digest_html import (
    MediumDigestArticleCandidate,
    extract_first_article,
)


def test_extracts_first_article_from_medium_digest_html():
    html = """
    <html><body>
      <a href="https://medium.com/@reader?source=email">Stories for Reader</a>
      <div class="generated-card-class">
        <a href="https://medium.com/@alice?source=email">Alice Example</a>
        <div style="margin-top: 16px;">
          <a href="https://medium.com/@alice/useful-python-tools-123456789abc?source=email-tracking">
            <h2>Useful Python Tools</h2>
            <div><h3>Small tools that make everyday development easier…</h3></div>
          </a>
        </div>
      </div>
      <div>
        <a href="https://medium.com/@bob?source=email">Bob Example</a>
        <a href="https://medium.com/@bob/a-second-story-abcdef123456?source=email-tracking">
          <h2>A Second Story</h2>
          <h3>This must not be selected by the first-article function.</h3>
        </a>
      </div>
    </body></html>
    """

    candidate = extract_first_article(html)

    assert candidate == MediumDigestArticleCandidate(
        title="Useful Python Tools",
        canonical_url="https://medium.com/@alice/useful-python-tools-123456789abc",
        author="Alice Example",
        summary="Small tools that make everyday development easier…",
    )


def test_returns_none_when_digest_contains_no_article_heading():
    html = '<a href="https://medium.com/@reader">Stories for Reader</a>'

    assert extract_first_article(html) is None
