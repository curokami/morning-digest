# ADR: Add Python Weekly with Source-aware polling

## Context

Python Weekly publishes an Issue approximately once a week, currently on
Thursdays. Its public site exposes an Archive and Issue pages. No advertised RSS
endpoint was found in the Archive markup during implementation, and the common
`/feed`, `/rss`, `/feed.xml`, and `/rss.xml` paths redirected to the site's
not-found page. Treating every Source as daily would create unnecessary requests
and couple collection cadence to the process scheduler.

## Decision

Python Weekly is an Article-set Source. On Friday in the configured application
timezone, its Collector reads the official Archive, follows the latest Issue,
and turns external links in the `News` and `Articles, Tutorials and Talks`
sections into ordinary Articles. Tracking query parameters are removed from
canonical URLs.

The LaunchAgent remains the external daily process scheduler. The application
only decides which Source Collectors are due during that invocation. Sources
that are not due receive no network request.

## Consequences

Python Weekly items use the existing enrichment, AI, persistence, digest, and
delivery stages. ADR 0020 later separates delivery streams by Source. Other
weekly or monthly Sources can add their own Collector and polling configuration
without changing the Article model. A missed weekly
polling day is not yet tracked independently; persistent last-poll state is a
future reliability improvement.
