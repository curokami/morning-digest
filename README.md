# Morning Digest

> Read less. Learn more.

Morning Digest is a personal information-triage tool that collects new Medium articles, summarizes them in Japanese, and recommends which originals deserve the reader's time.

## MVP

Version 1 uses Python 3.11+ (3.13 recommended), uv, mise, Medium RSS, OpenAI, Gmail, GitHub Actions, and JSON persistence.

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

Copy `config.yaml.example` to `config.yaml`. Secrets must come from environment variables or GitHub Secrets.

Required environment variables:

- `OPENAI_API_KEY`
- `GMAIL_USERNAME` — Gmail address used to send the digest
- `GMAIL_APP_PASSWORD` — Google app password (not the account password)
- `GMAIL_RECIPIENT` — destination email address

Run locally with:

```bash
cp config.yaml.example config.yaml
uv run morning-digest --config config.yaml
```

## Core idea

Morning Digest does not ask “Is this a good article?” It asks “Is this article worth this reader's time right now?”
