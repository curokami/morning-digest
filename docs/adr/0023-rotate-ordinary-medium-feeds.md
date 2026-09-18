# ADR 0023: Rotate ordinary Medium feeds

## Decision

Morning Digest polls preferred Medium feeds every day and divides ordinary
feeds into three stable, balanced groups that run on consecutive days. A feed
is preferred when its configured weight is greater than 1.0 or it explicitly
sets `daily: true`. The Omarchy tag feed is explicitly daily.

This reduces the current Medium RSS burst from 45 requests to approximately
17–18 requests per day without increasing retries or article-page requests.
Because author RSS feeds retain multiple recent entries, a three-day rotation
is expected to preserve coverage. The change is an access-load precaution, not
an attempt to bypass Medium's protection.
