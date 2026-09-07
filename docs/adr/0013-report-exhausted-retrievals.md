# ADR 0013: Report Exhausted Article Retrievals

## Status
Accepted

## Decision
Access-denied retrieval failures are counted by canonical URL. The system retries an article on at most three runs. On the third failure it persists `retrieval_exhausted`, removes the article from normal processing selection, and queues a one-time failure notice for the Digest.

The notice uses a cautious classification rather than claiming a definitive cause:

- `bot_protection_suspected`: 取得不能（ボット判定の疑い）
- `authentication_required`: 取得不能（認証が必要な可能性）
- `forbidden_unknown`: 取得不能（原因不明のアクセス拒否）

## Consequences
Repeatedly blocked preferred writers no longer consume the daily article limit indefinitely. The user is informed of the missed article and the evidence-based interpretation remains explicitly uncertain. A failure-only Digest may be delivered when an article first becomes exhausted.
