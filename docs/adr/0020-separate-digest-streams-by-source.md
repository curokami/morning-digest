# ADR: Separate Digest streams by Source

## Context

Combining a weekly batch of Python Weekly links with continually arriving Medium
articles creates unstable competition for one ten-Article limit. As more Sources
are added, a single mixed email would require increasingly arbitrary allocation
rules and obscure each Source's publication rhythm.

## Decision

Each Source has an independent Digest configuration containing a maximum Article
count and subject prefix. Medium keeps a daily `Morning Digest` with at most ten
Articles. Python Weekly sends a separate `🐍 Python Weekly Digest` on its polling
day with at most five Articles.

Persistence remains shared for canonical-URL duplicate detection, but pending
success and failure queues are filtered by Article source during delivery. One
Source cannot include or mark another Source's pending results as delivered.

## Consequences

Friday may produce two emails when both Sources have new content. New Sources
can define their own cadence and Digest limits without competing for a global
email quota. The first five Python Weekly links follow the newsletter's curated
editorial order; semantic pre-ranking of all Issue links remains future work.
