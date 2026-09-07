from datetime import date
from html import escape

from morning_digest.domain import Digest, ProcessingResult


class HtmlDigestBuilder:
    FAILURE_LABELS = {
        "bot_protection_suspected": "取得不能（ボット判定の疑い）",
        "authentication_required": "取得不能（認証が必要な可能性）",
        "forbidden_unknown": "取得不能（原因不明のアクセス拒否）",
    }

    def build(self, results: list[ProcessingResult], execution_date: str | None = None,
              failed_results: list[ProcessingResult] | None = None) -> Digest:
        ordered = sorted(results, key=lambda r: int(r.recommendation.reading_priority), reverse=True)
        failures = list(failed_results or [])
        cards = []
        for result in ordered:
            article, rec = result.article, result.recommendation
            cards.append(f'''<article style="margin:0 0 24px;padding:20px;border:1px solid #ddd;border-radius:10px">
<div style="font-size:13px;color:#666">{escape(article.source)} · Priority {int(rec.reading_priority)} — {escape(rec.reading_priority.label)}</div>
<h2 style="font-size:20px"><a href="{escape(article.canonical_url, quote=True)}">{escape(article.title)}</a></h2>
<p>{escape(result.summary.text)}</p><p><strong>読む理由:</strong> {escape(rec.reason_to_read)}</p>
<p style="font-size:13px;color:#555">{escape(' · '.join(rec.digest_tags))}</p></article>''')
        day = execution_date or date.today().isoformat()
        failure_section = ""
        if failures:
            failed_cards = []
            for result in failures:
                article = result.article
                label = self.FAILURE_LABELS.get(
                    result.error_classification, "取得不能（原因不明）")
                failed_cards.append(f'''<article style="margin:0 0 16px;padding:16px;border:1px solid #ddd;border-radius:10px">
<h3 style="font-size:17px;margin:0 0 8px"><a href="{escape(article.canonical_url, quote=True)}">{escape(article.title)}</a></h3>
<p style="margin:0;color:#8a3b12"><strong>{escape(label)}</strong></p>
<p style="font-size:13px;color:#666">{escape(article.source)} · 3回試行</p></article>''')
            failure_section = f'''<section><h2>取得できなかった記事</h2>{''.join(failed_cards)}</section>'''
        html = f'''<!doctype html><html lang="ja"><body style="font-family:-apple-system,sans-serif;max-width:680px;margin:auto;padding:20px;color:#222">
<h1>Morning Digest</h1><p>{escape(day)} · {len(ordered)} articles</p>{''.join(cards)}{failure_section}</body></html>'''
        return Digest(execution_date=day, results=tuple(ordered), html_content=html,
                      failed_results=tuple(failures))
