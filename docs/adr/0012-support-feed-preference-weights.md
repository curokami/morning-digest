# ADR: Support per-feed preference weights

Status: Accepted

## Context
The reader values some writers more highly and the daily Article limit may exclude their work. Feed order alone is an unclear and fragile preference mechanism.

## Decision
Medium feed configuration MAY be either a URL string with default weight 1.0 or a mapping containing `url` and a positive `weight`. Higher-weight Articles SHALL be selected first when limiting candidates. AI processing SHALL receive the weight as reader-preference context, but the weight SHALL NOT mechanically determine Reading Priority.

## Consequences
Reader preferences are explicit and backward compatible. A high weight improves selection probability and relevance context without guaranteeing a favorable Recommendation.

Accepted ADRs are normally preserved. A later ADR may supersede this decision.
