# Morning Digest Specification

Version: 1.0

The keywords SHALL, SHOULD, and MAY are normative.

## 1. Purpose
Morning Digest is a single-user application that reduces information triage. It discovers new articles, summarizes their content, and recommends whether the original is worth reading.

## 2. MVP Scope
Version 1 SHALL use Medium RSS as its only Source, OpenAI as its only AI provider, Gmail as its only Delivery mechanism, external scheduling, and JSON for persistence. GitHub Actions SHALL remain available for manual diagnostics.

The application SHALL support Python 3.11 or later; Python 3.13 SHOULD be the reference runtime. uv and mise SHALL be used for project/development environment management.

## 3. Success Criteria
A normal scheduled run SHALL require no manual intervention. New articles SHALL be deduplicated, processed independently, classified, summarized, recommended, persisted, rendered into HTML, and delivered when at least one article succeeds.

## 4. Definitions

### Source
An external origin from which Morning Digest obtains information. Version 1 supports Medium RSS only.

### Article
A content item obtained from a Source. It SHALL have a title, canonical URL, source identifier, and sufficient metadata for duplicate detection. Author, publication date, Source Tags, and content SHOULD be preserved when available.

### Summary
A concise Japanese representation of an Article's main content. Summary and Recommendation are distinct concepts.

### Recommendation
The user-oriented assessment of whether an Article is worth reading. It SHALL contain Reading Priority, Reason to Read, and one or more Digest Tags.

### Digest
The daily collection of successfully processed Articles with their Summaries and Recommendations, rendered as HTML for Version 1.

### Taxonomy
The controlled vocabulary used for Digest Tags. Version 1 stores it in `data/taxonomy.yaml`.

### Source Tag
A tag supplied by the original Source. It MAY inform classification but does not define Morning Digest's vocabulary.

### Digest Tag
A tag selected from the controlled Taxonomy. Every successful Recommendation SHALL contain at least one. `Uncategorized` SHALL be used when no controlled tag applies.

### Reading Priority
A five-level recommendation of expected reading value: 5 Read Today; 4 High Priority; 3 Worth Reading; 2 Optional; 1 Low Priority.

AI judgment SHALL be guided by Relevance 40%, Novelty 20%, Impact 20%, and Actionability 20%. These weights guide judgment; they do not require deterministic arithmetic scoring.

### Reason to Read
A concise Japanese explanation of why opening the original Article may be worth the user's time.

### Collector
A component that obtains and normalizes Articles from a Source.

### Enricher
A component that obtains or normalizes information required downstream.

### Summarizer
The logical responsibility that produces a Summary.

### Pipeline
The ordered application flow from collection through delivery.

## 5. Functional Requirements

### FR-001 Collection
The system SHALL retrieve all configured Medium RSS feeds and support one or more feeds.

### FR-002 Duplicate Detection
Previously successfully processed Articles SHALL NOT be reprocessed. Canonical URL SHALL be the Version 1 duplicate key.

### FR-003 Retrieval and Enrichment
The system SHALL obtain sufficient article content for meaningful analysis. Content embedded in RSS SHALL be used without requesting the original page when it is sufficient; the original page SHALL be an enrichment fallback for short or missing RSS content. Failure of one Article SHALL NOT terminate unrelated Articles.
Access-denied retrieval failures SHALL be counted by canonical URL. After three failed runs, the Article SHALL be marked `retrieval_exhausted`, excluded from subsequent processing limits, and reported once in the Digest with its cautious cause classification.

### FR-004 Metadata
Available author, publication date, canonical URL, and Source Tags SHOULD be preserved.

### FR-005 Taxonomy
Every successful Article SHALL receive one or more controlled Digest Tags. Unknown model-generated tags SHALL NOT be accepted. `Uncategorized` SHALL be the fallback.

### FR-006 Summary
Every successful Article SHALL receive a Japanese Summary, normally three to five sentences.

### FR-007 Recommendation
Every successful Article SHALL receive exactly one Recommendation containing Reading Priority, Reason to Read, and Digest Tags.

### FR-008 Reading Priority
The five-level Reading Priority SHALL be guided by Relevance 40%, Novelty 20%, Impact 20%, and Actionability 20%.

### FR-009 Reason to Read
Reason to Read SHOULD normally be one or two Japanese sentences.

### FR-010 Digest
A Digest entry SHALL contain title, Source, Summary, Reading Priority, Reason to Read, Digest Tags, and original URL. The Digest SHALL be HTML and SHOULD be mobile-readable.

### FR-011 Delivery
When at least one new Article is successfully processed, exactly one Digest email SHALL be sent through Gmail. A newly exhausted retrieval MAY also trigger a Digest containing the failed Article notice. If neither exists, the system SHALL NOT send an empty Digest; the run MAY still be successful. Delivery failure SHALL be logged and SHALL NOT require repeating successful AI processing.

### FR-012 Configuration
Runtime application behavior SHALL be configured through `config.yaml`; secrets SHALL NOT be stored there. Scheduling is not application configuration.

### FR-013 Taxonomy Storage
The controlled Taxonomy SHALL be stored in `data/taxonomy.yaml`, separate from runtime configuration. Source Tags SHALL NOT modify it automatically.

### FR-014 Persistence
Version 1 SHALL persist processing state in JSON, including canonical URL, timestamp, status, Digest Tags, and Reading Priority, sufficient for duplicate detection and delivery retry.

### FR-015 Logging
Version 1 SHALL use standard text logs recording execution start/finish, counts, failures, and delivery result. Unexpected failures SHALL include stack traces. Secrets SHALL NOT be logged.

### FR-016 Error Isolation
Article-level failure SHALL NOT terminate other Article processing. Only unrecoverable startup failures MAY terminate the run.

### FR-017 OpenAI
Version 1 SHALL use OpenAI only. Summary and Recommendation are logically separate responsibilities, but the implementation SHOULD obtain summary, priority, reason, and tags in one AI request per Article when practical.

### FR-018 Scheduling
The application SHALL NOT implement an internal scheduler. GitHub Actions SHALL support manual diagnostic execution but SHALL NOT schedule production delivery while Medium denies article enrichment from GitHub-hosted runners. On macOS, production delivery SHALL use a per-user LaunchAgent targeting approximately 07:40 local time and credentials from Keychain or environment variables.

### FR-020 Source Preference Weight
Each configured feed MAY define a positive preference weight; omitted weights SHALL default to 1.0. Higher-weight Articles SHALL be selected before lower-weight Articles when a run exceeds its Article limit. The weight SHALL be supplied to AI processing as reader-preference context, but SHALL NOT dictate a Reading Priority by itself.

### FR-019 Completion
A run with successfully processed new Articles SHALL produce persisted results, one HTML Digest, one delivery attempt, and operational logs.

## 6. Non-Functional Requirements

### NFR-001 Performance
A normal run processing up to ten new Articles SHOULD complete within ten minutes, excluding unusual external-service latency.

### NFR-002 Reliability
Individual Article failures SHALL be isolated.

### NFR-003 Maintainability
Domain logic SHALL remain separate from infrastructure concerns. Configuration SHALL be externalized. Architectural decisions SHALL be recorded as ADRs.

### NFR-004 Observability
Logs SHALL provide enough information to diagnose collection, AI, persistence, and delivery failures.

### NFR-005 Security
Secrets SHALL NOT be committed. Credentials SHALL be supplied by environment variables, GitHub Secrets, or the macOS Keychain for local execution. Environment variables SHALL take precedence over Keychain values.

### NFR-006 Portability
Python 3.11+ SHALL be supported; Python 3.13 SHOULD be the reference runtime.

### NFR-007 Extensibility
New Sources SHOULD be addable through new Collectors without changing the Recommendation model. New Delivery mechanisms SHOULD NOT require changes to domain concepts.

## 7. Logical Data Model
Article: title, canonical_url, source, author?, publication_date?, source_tags, content.
Summary: language, text.
Recommendation: reading_priority, digest_tags, reason_to_read.
ProcessingResult: Article, Summary?, Recommendation?, status, error?, error_classification?, attempt_count.
Digest: execution_date, successful results, exhausted retrieval results, html_content.
DeliveryResult: status, provider metadata/error.
Configuration: loaded from config.yaml, including optional per-feed preference weights.
Taxonomy: loaded from data/taxonomy.yaml.

## 8. Acceptance Criteria
Version 1 is accepted when:
- manual GitHub Actions diagnostic execution works;
- Medium RSS collection and duplicate detection work;
- each successful Article receives Summary and Recommendation;
- Reading Priority, Reason to Read, controlled Digest Tags, and `Uncategorized` fallback work;
- HTML Digest and Gmail delivery work;
- zero-success runs do not send empty mail;
- JSON persistence prevents repeated successful AI processing;
- delivery retry can reuse persisted processing results;
- operational logging works;
- one Article failure does not stop others;
- normal operation requires no manual intervention.

## 9. Future Work
Possible future work includes additional Sources, operational hardening, archive/search, feedback-driven personalization, additional Delivery mechanisms, and database storage. These are not Version 1 requirements.

Architectural changes SHALL follow: update SPEC → create new ADR if architecture changes → update ARCHITECTURE → update TODO → implement.
