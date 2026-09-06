# ADR: Use GitHub Actions for scheduling

Status: Accepted

## Context
Daily execution does not justify an internal scheduler or always-running server.

## Decision
GitHub Actions SHALL schedule production runs. The application SHALL NOT implement an internal scheduler. Target time is approximately 07:40 JST.

## Consequences
No server required; depends on GitHub Actions scheduling characteristics.

Accepted ADRs are normally preserved. A later ADR may supersede this decision.
