# ADR: Use OpenAI as the sole AI provider

Status: Accepted

## Context
Summary and Recommendation require AI; premature multi-provider abstraction adds cost.

## Decision
Version 1 SHALL use OpenAI only. Domain concepts SHALL remain independent of OpenAI client types.

## Consequences
Smaller implementation; operational dependence on OpenAI.

Accepted ADRs are normally preserved. A later ADR may supersede this decision.
