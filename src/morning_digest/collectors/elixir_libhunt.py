from __future__ import annotations

import re
from urllib.request import Request, urlopen

import feedparser
from bs4 import BeautifulSoup

from morning_digest.domain import Article


class ElixirLibHuntCollector:
    SECTIONS = ("Popular News and Articles", "Trending packages and projects")

    def __init__(self, feed_url: str, fetcher=None, feed_parser=None) -> None:
        self.feed_url = feed_url
        self.fetcher = fetcher or self._fetch
        self.feed_parser = feed_parser or feedparser.parse

    def collect(self, _settings) -> list[Article]:
        feed = self.feed_parser(self.feed_url)
        if not feed.entries:
            raise RuntimeError("Awesome Elixir feed contained no Issues")
        latest = feed.entries[0]
        issue_url = latest.get("link")
        if not issue_url:
            raise RuntimeError("Awesome Elixir feed entry had no Issue URL")
        return self._extract_issue(
            self.fetcher(issue_url), latest.get("published"), issue_url)

    def _extract_issue(self, html: str, published: str | None,
                       issue_url: str) -> list[Article]:
        soup = BeautifulSoup(html, "html.parser")
        articles: list[Article] = []
        positions: dict[str, int] = {}
        for heading in soup.select("h3.section-title"):
            section = heading.get_text(" ", strip=True)
            if section not in self.SECTIONS:
                continue
            listing = heading.find_next("ul")
            if listing is None:
                continue
            for item in listing.find_all("li", recursive=False):
                if item.get("id") in {"sponsored", "saashub-newsletter"}:
                    continue
                title_link = item.select_one("a.title")
                if title_link is None:
                    continue
                title = title_link.get_text(" ", strip=True)
                url = self._project_url(item) or title_link.get("href")
                if not title or not url or "saashub.com" in url:
                    continue
                description_node = item.select_one("p.description")
                description = description_node.get_text(" ", strip=True) if description_node else ""
                content = f"{title}. {description}".strip()
                article = Article(
                    title=title,
                    canonical_url=url,
                    source="Awesome Elixir",
                    publication_date=published,
                    source_tags=("Elixir", section),
                    content=content,
                    preference_weight=2.0 if section == "Popular News and Articles" else 1.0,
                )
                key = self._title_key(title)
                if key in positions:
                    index = positions[key]
                    if len(article.content) > len(articles[index].content):
                        articles[index] = article
                else:
                    positions[key] = len(articles)
                    articles.append(article)
        if not articles:
            raise RuntimeError(f"No editorial entries found in Awesome Elixir Issue: {issue_url}")
        return articles

    @staticmethod
    def _title_key(title: str) -> str:
        without_suffix = re.sub(r"\s*\([^)]*\)\s*$", "", title)
        return " ".join(without_suffix.casefold().split())

    @staticmethod
    def _project_url(item) -> str | None:
        github = item.select_one('a[href^="https://github.com/"]')
        return github.get("href") if github else None

    @staticmethod
    def _fetch(url: str) -> str:
        request = Request(url, headers={"User-Agent": "MorningDigest/0.1"})
        with urlopen(request, timeout=30) as response:
            return response.read().decode(
                response.headers.get_content_charset() or "utf-8", errors="replace")
