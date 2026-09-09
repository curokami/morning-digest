# ADR: Support all-of Source Tag weight rules

## Decision

Configuration MAY define tag-weight rules containing a non-empty `all` list and
a positive `weight`. A rule matches only when every listed Source Tag is present,
using case-insensitive comparison. Matching rule multipliers are combined with
the feed preference weight.

## Consequences

Readers can prioritize a specific intersection such as Elixir and Programming
without prioritizing every article carrying either tag. The rule operates on RSS
metadata and therefore does not require an additional article-page request.
