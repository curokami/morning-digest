#!/usr/bin/env python3
"""Compare the current extractor with Trafilatura without changing production."""

from __future__ import annotations

import argparse
import sys
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import trafilatura

from morning_digest.enrichment.web import ArticleEnricher


def download(url: str) -> tuple[str, int, float]:
    request = Request(url, headers={"User-Agent": "MorningDigest/0.1"})
    started = monotonic()
    with urlopen(request, timeout=20) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace"), len(raw), monotonic() - started


def metrics(text: str | None) -> tuple[int, int, int]:
    value = text or ""
    normalized = " ".join(value.split())
    lines = sum(1 for line in value.splitlines() if line.strip())
    return len(normalized), len(normalized.split()), lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Morning Digest and Trafilatura extraction lengths."
    )
    parser.add_argument("urls", nargs="+", help="Article URL(s) to inspect")
    args = parser.parse_args()

    exit_code = 0
    for url in args.urls:
        print(f"URL: {url}")
        try:
            html, downloaded_bytes, elapsed = download(url)
        except HTTPError as exc:
            print(f"  download: HTTP {exc.code}")
            exit_code = 1
            continue
        except URLError as exc:
            print(f"  download: failed ({exc.reason})")
            exit_code = 1
            continue

        current_started = monotonic()
        current_text = ArticleEnricher._text(html)
        current_elapsed = monotonic() - current_started

        trafilatura_started = monotonic()
        trafilatura_text = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
        )
        trafilatura_elapsed = monotonic() - trafilatura_started

        current_chars, current_words, current_lines = metrics(current_text)
        trafilatura_chars, trafilatura_words, trafilatura_lines = metrics(trafilatura_text)
        print(f"  download: {downloaded_bytes} bytes in {elapsed:.2f}s")
        print(
            f"  current: {current_chars} chars, {current_words} words, "
            f"{current_lines} blocks in {current_elapsed:.3f}s"
        )
        print(
            f"  trafilatura: {trafilatura_chars} chars, {trafilatura_words} words, "
            f"{trafilatura_lines} blocks in {trafilatura_elapsed:.3f}s"
        )
        if not trafilatura_text:
            print("  result: Trafilatura found no main text")
        elif current_chars:
            print(f"  length ratio: {trafilatura_chars / current_chars:.2f}")
        print()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
