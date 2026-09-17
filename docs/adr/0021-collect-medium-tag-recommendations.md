# ADR: Collect a bounded Medium tag feed

## Decision

Morning Digest MAY configure a Medium tag RSS feed with a per-feed limit.
The Omarchy feed contributes at most its two newest entries per run. Its
`Omarchy` Source Tag receives preference weight 2.0 through the ordinary tag
weight rule.

Medium's tag page labels items as recommendations but rejects this application's
automated request with HTTP 403. The public tag RSS is reliable, but exposes
recency rather than view counts or recommendation order. Therefore the selected
two are explicitly the newest stories, not objectively popular stories. Original
article enrichment and the normal ten-item Morning Digest limit still apply.
