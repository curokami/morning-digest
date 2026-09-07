# Morning Digest Architecture

Version: 1.0

## 1. Overview
Morning Digest is a pipeline-oriented application. Domain concepts remain independent of Medium, OpenAI, Gmail, GitHub Actions, and JSON implementation details.

Conceptual flow:

Source → Collector → Enricher → AI Processing → Persistence → Digest Builder → Delivery

Summary and Recommendation are logically separate responsibilities. Version 1 MAY satisfy both through one validated OpenAI structured-output request per Article.

## 2. Principles
- Single responsibility.
- Pipeline-first orchestration.
- Recommendation-centric product value.
- Controlled Taxonomy.
- Failure isolation per Article.
- Configuration over code.
- Domain dependencies point inward.
- No infrastructure for hypothetical future scale.

Pipeline stages SHALL NOT rely on uncontrolled destructive mutation of inputs; the concrete Python immutability mechanism is an implementation choice.

## 3. Components

### Collector
Retrieves Medium RSS, normalizes entries into Articles, preserves available metadata and configured preference weight, and coordinates duplicate filtering.

### Enricher
Retrieves sufficient article content and normalizes metadata.

### AI Processing
Implements logical Summarizer and Recommendation Engine responsibilities. It receives Article content plus Taxonomy and returns validated Summary, Reading Priority, Reason to Read, and Digest Tags.

### Persistence Store
Stores successful processing results and relevant failures in JSON. It supports duplicate detection and prevents repeated AI processing when only Delivery fails.

### Digest Builder
Orders successful results by Reading Priority and renders HTML. It SHALL NOT perform AI inference.

### Delivery
Sends a completed Digest through Gmail and returns a DeliveryResult.

### Logger
Records execution and failure information without secrets.

## 4. Recommendation Flow
For each candidate Article:
1. check successful-processing state;
2. enrich content;
3. invoke AI processing;
4. validate structured output;
5. validate Digest Tags;
6. persist the successful ProcessingResult.

When the Article limit is lower than the candidate count, higher feed preference weights are processed first. AI processing receives the weight as user-preference context; it remains responsible for judging the Article itself.

After all Articles:
7. if none succeeded, finish without empty email;
8. otherwise build one HTML Digest;
9. deliver through Gmail;
10. record DeliveryResult.

## 5. Dependency Direction
External services → infrastructure adapters → application orchestration → domain model.

Domain objects SHALL NOT depend on RSS libraries, OpenAI client types, Gmail APIs, GitHub Actions, or filesystem-specific types.

## 6. Recommended Repository Structure

```text
morning-digest/
├── README.md
├── TODO.md
├── pyproject.toml
├── mise.toml
├── config.yaml.example
├── data/taxonomy.yaml
├── docs/
│   ├── PROJECT_CHARTER.md
│   ├── SPEC.md
│   ├── ARCHITECTURE.md
│   ├── PROMPTS.md
│   ├── ROADMAP.md
│   └── adr/
├── src/morning_digest/
│   ├── domain/
│   ├── collectors/
│   ├── enrichment/
│   ├── ai/
│   ├── digest/
│   ├── delivery/
│   ├── persistence/
│   ├── config/
│   └── pipeline.py
├── tests/{unit,integration}/
└── .github/workflows/morning-digest.yml
```

`pipeline.py` orchestrates stages but does not implement their internals.

## 7. Error Flow
Article-level retrieval, enrichment, AI, taxonomy-validation, and persistence failures SHALL be logged and isolated. Failed Articles are excluded from the current Digest.

Invalid required Configuration, unreadable Taxonomy, or inability to initialize Persistence MAY terminate startup.

Delivery failure SHALL preserve already persisted successful processing results so Delivery can be retried without another AI request.

## 8. Deployment
Version 1 runs as a scheduled GitHub Actions workflow. Python 3.11+ is supported; 3.13 is recommended. uv manages Python project/dependencies; mise manages the development runtime.

Secrets come from GitHub Secrets/environment variables. Scheduling belongs to the workflow, not `config.yaml`. Target execution is approximately 07:40 JST.

## 9. Constraints
Version 1 intentionally has Medium RSS only, OpenAI only, Gmail only, JSON persistence, a single user, no database, no Web UI, manually reviewed Taxonomy, and no internal scheduler.

## 10. Evolution
Changes follow SPEC → new ADR when architecture changes → ARCHITECTURE → TODO → implementation. Accepted ADRs are normally preserved; later ADRs supersede earlier decisions.
