# ADR 0016: Use macOS Keychain for Local Credentials

## Status
Accepted

## Context
Shell environment variables disappear when their terminal session ends, making
repeated local execution inconvenient. Storing credentials in `.env` or shell
startup files would leave them as plaintext files.

## Decision
Runtime credentials are resolved from environment variables first. On macOS,
missing values are read from generic-password items whose account is
`morning-digest` and whose service names match the required environment variable
names. Other platforms continue to require environment variables.

## Consequences
Local credentials survive terminal sessions and can support future unattended
execution without entering Git history. The application depends on the macOS
`security` command for fallback, and Keychain may request user authorization.
Long OpenAI project keys must be collected without the `security -w` interactive
prompt, which can truncate long input, and then supplied as the command value.
