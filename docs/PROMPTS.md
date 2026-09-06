# Morning Digest AI Prompts

`SPEC.md` remains authoritative.

## Input
AI processing SHOULD receive title, article body, available author/publication metadata, Source Tags, controlled Digest Tags, and Reading Priority criteria. Source Tags are contextual hints only.

## Output contract

```json
{
  "summary": "日本語の要約",
  "reading_priority": 3,
  "reason_to_read": "読む理由",
  "digest_tags": ["Elixir"]
}
```

`summary` and `reason_to_read` SHALL be non-empty Japanese strings. `reading_priority` SHALL be 1–5. `digest_tags` SHALL contain at least one controlled value.

## System behavior
Help the reader decide whether the original article is worth reading; do not judge general popularity or intrinsic quality.

Evaluate Reading Priority using Relevance 40%, Novelty 20%, Impact 20%, Actionability 20%. These weights guide judgment, not mandatory arithmetic.

Use only supplied controlled Digest Tags. If none applies, use `Uncategorized`. Do not invent tags.

## Summary
Normally three to five Japanese sentences. State the main subject/claim and important new information. Avoid filler and unsupported facts.

## Reason to Read
Normally one or two Japanese sentences explaining why opening the original is worth the reader's time.

## Priority levels
5 Read Today
4 High Priority
3 Worth Reading
2 Optional
1 Low Priority

## Validation
Application code SHALL validate required fields, priority range, and Taxonomy membership. Invalid output SHALL NOT be persisted as successful. Bounded retries MAY be used; exhaustion affects only the current Article.

## Evolution
Prompt wording MAY change without ADR if SPEC behavior is preserved. Changes to Recommendation meaning/structure, classification semantics, or AI's architectural role SHOULD use the ADR process.
