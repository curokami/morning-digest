# ADR 0024: Add Awesome Elixir as a weekly article-set source

## Decision

Awesome Elixir Newsletter is a recurring weekly Source. On Friday, its official
RSS identifies the latest Issue. The Issue page is parsed into individual
Articles from `Popular News and Articles` and `Trending packages and projects`.
Sponsored entries are excluded, repeated titles prefer the entry with richer
editorial context, and GitHub project links are used instead of LibHunt redirect
pages when available.

Awesome Elixir produces a separate `⚗️ Awesome Elixir Digest` with at most five
Articles. Popular news receives a higher source preference than package-list
entries, while the ordinary AI recommendation still determines reading value.
