from datetime import date
from html import escape

from morning_digest.domain import Digest, ProcessingResult


class HtmlDigestBuilder:
    def build(self, results: list[ProcessingResult], execution_date: str | None = None) -> Digest:
        ordered = sorted(results, key=lambda r: int(r.recommendation.reading_priority), reverse=True)
        cards = []
        for result in ordered:
            article, rec = result.article, result.recommendation
            cards.append(f'''<article style="margin:0 0 24px;padding:20px;border:1px solid #ddd;border-radius:10px">
<div style="font-size:13px;color:#666">{escape(article.source)} · Priority {int(rec.reading_priority)} — {escape(rec.reading_priority.label)}</div>
<h2 style="font-size:20px"><a href="{escape(article.canonical_url, quote=True)}">{escape(article.title)}</a></h2>
<p>{escape(result.summary.text)}</p><p><strong>読む理由:</strong> {escape(rec.reason_to_read)}</p>
<p style="font-size:13px;color:#555">{escape(' · '.join(rec.digest_tags))}</p></article>''')
        day = execution_date or date.today().isoformat()
        html = f'''<!doctype html><html lang="ja"><body style="font-family:-apple-system,sans-serif;max-width:680px;margin:auto;padding:20px;color:#222">
<h1>Morning Digest</h1><p>{escape(day)} · {len(ordered)} articles</p>{''.join(cards)}</body></html>'''
        return Digest(execution_date=day, results=tuple(ordered), html_content=html)
