# ADR: Use JSON persistence for the MVP

Status: Accepted

## Context
Version 1 needs duplicate detection, processing state, and delivery retry but not concurrent querying.

## Decision
Version 1 SHALL use JSON persistence and SHALL NOT require a database.

## Consequences
Minimal infrastructure and human-readable state; later scale may require migration.

Accepted ADRs are normally preserved. A later ADR may supersede this decision.
