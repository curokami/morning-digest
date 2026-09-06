# Morning Digest — Implementation TODO

`docs/SPEC.md` is normative. Follow SPEC → ADR if architecture changes → ARCHITECTURE → TODO → implementation.

## 0. Bootstrap
- [ ] Complete uv project for Python 3.11+; reference runtime 3.13.
- [ ] Create `src/morning_digest/`, unit/integration tests, pytest, lint/format configuration.
- [ ] Ensure secrets and `config.yaml` are ignored.
- [ ] Confirm `uv run pytest` works.

## 1. Domain
- [ ] Implement Article, Summary, Recommendation, Digest, ProcessingResult, DeliveryResult, ReadingPriority.
- [ ] Keep domain free of Medium/OpenAI/Gmail/filesystem client types.
- [ ] Validate five priority levels and at least one Digest Tag.

## 2. Configuration
- [ ] Parse/validate `config.yaml`.
- [ ] Load secrets from environment variables; never log them.

## 3. Taxonomy
- [ ] Load/validate `data/taxonomy.yaml`.
- [ ] Expose controlled tags and `Uncategorized`.
- [ ] Reject unknown AI-generated tags.

## 4. Persistence
- [ ] JSON state keyed by canonical URL.
- [ ] Persist timestamp, status, Recommendation data, and enough output for delivery retry.
- [ ] Use safe file replacement; test restart/duplicates.

## 5. Medium Collector
- [ ] Fetch configured feeds and normalize Article metadata.
- [ ] Preserve Source Tags and remove already-successful URLs.
- [ ] Isolate malformed-feed failures where possible.

## 6. Enrichment
- [ ] Retrieve sufficient article body and isolate per-Article failures.

## 7. OpenAI Processing
- [ ] Implement `docs/PROMPTS.md`.
- [ ] Prefer one structured request per Article.
- [ ] Validate fields, priority, Taxonomy membership.
- [ ] Use bounded retry and isolate failure.

## 8. Digest Builder
- [ ] Sort by Reading Priority and render safe mobile-readable HTML.
- [ ] Include all required fields/original links; do not invoke AI.

## 9. Gmail Delivery
- [ ] Send one Digest when at least one Article succeeds.
- [ ] Send no empty Digest.
- [ ] Preserve persisted results on failure and retry without repeated AI.

## 10. Pipeline
- [ ] Load config/taxonomy/state.
- [ ] Collect → deduplicate → enrich → AI → validate → persist per Article.
- [ ] Build/deliver after processing and report useful exit status/statistics.

## 11. Logging
- [ ] Text logs for start/finish, counts, failures, delivery; stack traces for unexpected failures; redact secrets.

## 12. GitHub Actions
- [ ] Add scheduled workflow targeting approximately 07:40 JST.
- [ ] Install with uv, inject GitHub Secrets, support `workflow_dispatch`.

## 13. Acceptance
- [ ] Verify every acceptance criterion in `docs/SPEC.md`.
- [ ] Ensure tests pass, no secrets are committed, and docs match implementation.
