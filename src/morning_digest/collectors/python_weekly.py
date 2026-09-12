from __future__ import annotations

import logging
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from morning_digest.domain import Article


class PythonWeeklyCollector:
    DEFAULT_SECTIONS = ("News", "Articles, Tutorials and Talks")
    ISSUE_PATH = re.compile(r"^/p/python-weekly-issue-")

    def __init__(self, archive_url: str, sections: list[str] | None = None,
                 weight: float = 1.0, fetcher=None, logger=None) -> None:
        if weight <= 0:
            raise ValueError("Python Weekly weight must be greater than zero")
        self.archive_url = archive_url
        self.sections = frozenset(sections or self.DEFAULT_SECTIONS)
        self.weight = float(weight)
        self.fetcher = fetcher or self._fetch
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, _settings=None) -> list[Article]:
        try:
            archive_html = self.fetcher(self.archive_url)
            issue_url = self.latest_issue_url(archive_html, self.archive_url)
            issue_html = self.fetcher(issue_url)
            return self.parse_issue(issue_html)
        except Exception:
            self.logger.exception("Could not read Python Weekly: %s", self.archive_url)
            return []

    @classmethod
    def latest_issue_url(cls, html: str, archive_url: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.find_all("a", href=True):
            path = urlsplit(anchor["href"]).path
            if cls.ISSUE_PATH.match(path):
                return urljoin(archive_url, anchor["href"])
        raise ValueError("Python Weekly archive contains no Issue link")

    def parse_issue(self, html: str) -> list[Article]:
        soup = BeautifulSoup(html, "html.parser")
        published = self._published_date(soup)
        current_section = ""
        articles: list[Article] = []

        for heading in soup.select("h5, h6"):
            if heading.name == "h5":
                current_section = heading.get_text(" ", strip=True)
                continue
            if current_section not in self.sections:
                continue
            anchor = heading.find("a", href=True)
            if anchor is None or not self._is_external_article(anchor["href"]):
                continue
            title = anchor.get_text(" ", strip=True) or heading.get_text(" ", strip=True)
            container = heading.parent
            content = container.get_text(" ", strip=True) if container else title
            articles.append(Article(
                title=title,
                canonical_url=self._canonical_url(anchor["href"]),
                source="Python Weekly",
                publication_date=published,
                source_tags=("Python", current_section),
                content=content,
                preference_weight=self.weight,
            ))

        return list({article.canonical_url: article for article in articles}.values())

    @staticmethod
    def _fetch(url: str) -> str:
        request = Request(url, headers={"User-Agent": "MorningDigest/0.1"})
        with urlopen(request, timeout=20) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")

    @staticmethod
    def _published_date(soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"property": "article:published_time"})
        if meta and meta.get("content"):
            return str(meta["content"])
        time = soup.find("time", datetime=True)
        return str(time["datetime"]) if time else None

    @staticmethod
    def _is_external_article(url: str) -> bool:
        host = (urlsplit(url).hostname or "").casefold()
        return bool(host and host not in {"pythonweekly.com", "www.pythonweekly.com"}
                    and not host.endswith("beehiiv.com"))

    @staticmethod
    def _canonical_url(url: str) -> str:
        parts = urlsplit(url)
        query = urlencode([
            (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if not key.casefold().startswith("utm_") and key.casefold() != "_bhiiv"
        ])
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))
