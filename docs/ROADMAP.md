# Morning Digest Roadmap

This document is non-normative. `SPEC.md` defines required behavior.

## Phase 1 — MVP
Medium RSS, enrichment, Japanese Summary, Recommendation, Reading Priority, Reason to Read, controlled Digest Tags, HTML email, Gmail, JSON persistence, GitHub Actions, logging.

## Phase 2 — Operational Hardening
Potential retry policy, delivery retry tooling, persistence backup, prompt evaluation fixtures, improved observability, failure notification, and HTML-email compatibility testing.

## Phase 3 — Additional Sources
Python Weekly is implemented. Further candidates: GitHub, Hacker News, Bluesky, Reddit. New Sources SHOULD use Source-specific Collectors, declare an appropriate polling cadence, and preserve the Recommendation model.

## Phase 4 — Discovery and Archive
Potential archive, search, filtering, reading history, and bookmarking, only when demonstrated user need exists.

## Phase 5 — Personalization
Potential feedback, adaptive relevance, topic preferences, and reading-history-informed recommendations.

## Non-goals
Not committed to becoming a general RSS reader, supporting every Source, replacing originals, becoming a social reading platform, or adding infrastructure for hypothetical scale.
