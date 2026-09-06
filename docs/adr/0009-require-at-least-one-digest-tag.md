# ADR: Require at least one Digest Tag

Status: Accepted

## Context
An untagged success state complicates filtering and presentation.

## Decision
Every successful Recommendation SHALL contain at least one Digest Tag. `Uncategorized` SHALL be used when none applies.

## Consequences
Predictable structure; Uncategorized can reveal taxonomy gaps.

Accepted ADRs are normally preserved. A later ADR may supersede this decision.
