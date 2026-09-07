# ADR 0014: Prefer RSS Article Content

## Status
Accepted

## Context
Medium RSS discovery succeeds on GitHub-hosted runners, while direct requests to
article pages may receive access-denial challenges. Many RSS feeds embed a body
or substantial summary that is already sufficient for analysis.

## Decision
The Collector preserves the richest body available from RSS `content`,
`summary`, or `description`. The Enricher uses that normalized RSS body directly
when it contains at least 200 characters. It requests the original page only
when RSS content is shorter or absent.

## Consequences
GitHub Actions can process feeds without unnecessary direct page requests, so
it is less exposed to page-level bot protection. The behavior is based on RSS
capabilities rather than Medium-specific bypass logic and therefore preserves
future multi-source extensibility. Feeds containing only short excerpts still
require page enrichment and can still be denied.
