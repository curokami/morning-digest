# Morning Digest

> Read less. Learn more.

Morning Digest is a personal information-triage tool that collects new articles from Medium and Python Weekly, summarizes them in Japanese, and recommends which originals deserve the reader's time.

## MVP

Version 1 uses Python 3.11+ (3.13 recommended), uv, mise, Medium RSS, the Python Weekly archive, OpenAI, Gmail, GitHub Actions, and JSON persistence.

Each successful article receives a Japanese Summary and a Recommendation containing Reading Priority, Reason to Read, and controlled Digest Tags.

## Documentation authority

`docs/SPEC.md` is authoritative for product behavior. If this README and SPEC disagree, SPEC wins.

Read in this order:

1. `docs/PROJECT_CHARTER.md`
2. `docs/SPEC.md`
3. `docs/adr/`
4. `docs/ARCHITECTURE.md`
5. `config.yaml.example`
6. `data/taxonomy.yaml`
7. `docs/PROMPTS.md`
8. `docs/ROADMAP.md`
9. `TODO.md`

## Development process

SPEC → ADR when architecture changes → ARCHITECTURE → TODO → implementation.

Accepted ADRs are normally preserved; a later ADR supersedes an earlier decision.

## Development environment

Recommended: Python 3.13, uv, mise. Minimum supported Python: 3.11.

```bash
uv sync
uv run pytest
```

Copy `config.yaml.example` to `config.yaml`. Secrets must come from environment
variables, the macOS Keychain, or GitHub Secrets.

Required credential names:

- `OPENAI_API_KEY`
- `GMAIL_USERNAME` — Gmail address used to send the digest
- `GMAIL_APP_PASSWORD` — Google app password (not the account password)
- `GMAIL_RECIPIENT` — destination email address

On macOS, credentials can be stored once in Keychain. Each command prompts
twice without displaying or recording the value in shell history:

```bash
read -r -s "md_key?OpenAI API key: "; echo; security add-generic-password -U -a morning-digest -s OPENAI_API_KEY -w "$md_key"; unset md_key
security add-generic-password -U -a morning-digest -s GMAIL_USERNAME -w
security add-generic-password -U -a morning-digest -s GMAIL_APP_PASSWORD -w
security add-generic-password -U -a morning-digest -s GMAIL_RECIPIENT -w
```

The `read` form is required for the long OpenAI project key; the interactive
password prompt of `security ... -w` may truncate it. The command itself, but
not the entered key, is retained in shell history.

Environment variables take precedence when present. Otherwise, the app reads
the matching service from the `morning-digest` Keychain account.

Run locally with:

```bash
cp config.yaml.example config.yaml
uv run morning-digest --config config.yaml
```

## Extraction experiment

To compare the current HTML text extraction with Trafilatura without changing
the production pipeline:

```bash
uv run --with trafilatura python scripts/compare_extractors.py "ARTICLE_URL"
```

The page is downloaded once and passed to both extractors. The command reports
only byte counts, character counts, and timing; it does not print or save the
article text.

## GitHub Actions

The workflow is available for manual diagnostics from the repository's
**Actions** tab. Scheduled delivery is intentionally disabled because direct
Medium retrieval can be denied from GitHub-hosted runners. Add these repository
secrets under **Settings → Secrets and variables → Actions**:

- `OPENAI_API_KEY`
- `GMAIL_USERNAME`
- `GMAIL_APP_PASSWORD`
- `GMAIL_RECIPIENT`
- `MORNING_DIGEST_CONFIG` — the complete contents of your local `config.yaml`

`MORNING_DIGEST_CONFIG` keeps the real writer list and preference weights out
of Git history. The workflow recreates `config.yaml` only inside the temporary
Actions runner. It stops with a named error if any required secret is missing.

After adding all five secrets, open **Actions → Morning Digest → Run workflow**
for a manual diagnostic run.

## Local scheduling on macOS

Production delivery uses a per-user LaunchAgent at approximately 07:40 local
time. The installed plist is based on
`launchd/com.curokami.morning-digest.plist.example`, with absolute local paths
substituted for `UV_EXECUTABLE` and `PROJECT_DIRECTORY`. Runtime credentials are
read from the macOS Keychain; no credentials belong in the plist.

The installed job can be inspected with:

```bash
launchctl print gui/$(id -u)/com.curokami.morning-digest
```

Its launcher output is written to `logs/launchd.stdout.log` and
`logs/launchd.stderr.log`; application logs remain in the configured log file.

## Core idea

Morning Digest does not ask “Is this a good article?” It asks “Is this article worth this reader's time right now?”

When article retrieval is denied, logs distinguish evidence-backed
`bot_protection_suspected`, `authentication_required`, and
`forbidden_unknown` classifications. A suspicion is diagnostic evidence, not
proof of the remote service's internal decision.
