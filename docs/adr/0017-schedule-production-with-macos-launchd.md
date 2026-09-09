# ADR 0017: Schedule Production with macOS launchd

## Status
Accepted

## Context
Local retrieval succeeds where GitHub-hosted runner requests can receive Medium
access-denial challenges. Requiring a terminal session and temporary exported
credentials would make unattended execution unreliable.

## Decision
Production runs use a per-user macOS LaunchAgent with a 07:40 local-time
`StartCalendarInterval`. It invokes the project CLI through an absolute `uv`
path and working directory. Credentials remain in macOS Keychain and logs remain
inside the ignored project `logs` directory.

## Consequences
The digest can run without an open terminal while the Mac user environment is
available. Delivery depends on the Mac being powered on and able to access its
login Keychain and network. GitHub Actions remains manual-only.
