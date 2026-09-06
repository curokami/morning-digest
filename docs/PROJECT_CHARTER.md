# Morning Digest Project Charter

## Vision
Reduce the time spent triaging information while preserving high-value reading.

## Mission
Automatically collect newly published articles, summarize them, classify them with a controlled vocabulary, and recommend which originals deserve the reader's attention.

## Product principle
Morning Digest does not replace reading. It prioritizes reading.

## MVP outcome
Each scheduled run discovers new Medium articles, processes each independently, and, when at least one article succeeds, sends one HTML digest through Gmail.

## Success
The MVP is successful when the acceptance criteria in `SPEC.md` pass and normal daily operation requires no manual intervention.

## Scope discipline
Version 1 favors a small, understandable system. New core concepts are introduced only when existing domain concepts cannot represent the requirement. Architectural changes follow the ADR process.

## Authority
`SPEC.md` is authoritative for product behavior and normative terminology.
