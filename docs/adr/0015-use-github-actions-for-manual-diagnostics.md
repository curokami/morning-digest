# ADR 0015: Use GitHub Actions for Manual Diagnostics

## Status
Accepted

## Context
GitHub-hosted runners successfully collect RSS but direct Medium article
requests receive access-denial challenges. The same retrieval succeeds from the
local Mac. Scheduled cloud runs can therefore produce misleading retrieval
failure notices and duplicate local delivery.

## Decision
ADR 0006 is superseded for production scheduling. The GitHub Actions workflow
retains `workflow_dispatch` for manual diagnostics but has no scheduled trigger.
Production delivery will use an external scheduler on the local Mac, targeting
approximately 07:40 JST.

## Consequences
GitHub remains useful for source control and reproducible manual checks without
generating automatic failure mail. Production delivery depends on the local Mac
being available; its scheduling configuration remains future implementation.
