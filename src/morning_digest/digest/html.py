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
              failed_results: list[ProcessingResult] | None = None,
              title: str = "Morning Digest") -> Digest:
        ordered = sorted(results, key=lambda r: int(r.recommendation.reading_priority), reverse=True)
        failures = list(failed_results or [])
        weekly = any(r.article.source == "Python Weekly" for r in ordered + failures) or "Python Weekly" in title
        accent = "#285c47" if weekly else "#526b7b"
        if weekly:
            title_heading = f'''<h1 style="font-size:27px;line-height:1.4;margin:0 0 10px;font-family:Georgia,serif;color:{accent}">{escape(title)}</h1>'''
        else:
            title_heading = f'''<table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 10px"><tr>
<td style="padding:0 14px 0 0;vertical-align:middle"><img src="cid:morning-digest-coffee" width="64" height="64" alt="Hot coffee" style="display:block;width:64px;height:64px;border:0"></td>
<td style="vertical-align:middle"><h1 style="font-size:27px;line-height:1.4;margin:0;font-family:Georgia,serif;color:{accent}">{escape(title)}</h1></td>
</tr></table>'''
        priority_labels = {5: "まず読みたい", 4: "おすすめ", 3: "時間があれば", 2: "気になったら", 1: "参考までに"}
        cards = []
        for index, result in enumerate(ordered):
            article, rec = result.article, result.recommendation
            featured = index == 0
            kicker = ("今週の一押し" if weekly else "今日の一押し") if featured else ""
            label = priority_labels[int(rec.reading_priority)]
            feature_heading = f'<p style="margin:0 0 12px;font-size:13px;font-weight:bold;color:{accent}">{kicker}</p>' if featured else ""
            cards.append(f'''<article style="margin:0 0 28px;padding:{'24px' if featured else '8px 0 24px'};background:{'#f0f3ed' if featured else '#fffdf8'};border-bottom:1px solid #deded5">
{feature_heading}<div style="font-size:12px;color:#777c78">{escape(article.source)} · {label}</div>
<h2 style="font-size:{'25' if featured else '21'}px;line-height:1.5;margin:10px 0 16px;font-family:Georgia,'Hiragino Mincho ProN','Yu Mincho',serif"><a style="color:{accent};text-decoration:none" href="{escape(article.canonical_url, quote=True)}">{escape(article.title)}</a></h2>
<p style="margin:0 0 16px;line-height:1.9">{escape(result.summary.text)}</p>
<p style="margin:0;line-height:1.85;font-size:14px;color:#555b56"><span style="color:{accent};font-weight:bold">読む理由</span><br>{escape(rec.reason_to_read)}</p>
<p style="margin:16px 0 0;font-size:12px;color:#888e85">{escape(' · '.join(rec.digest_tags))}</p></article>''')
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
<p style="font-size:13px;color:#666">{escape(article.source)} · {result.attempt_count}回試行</p></article>''')
            failure_section = f'''<section><h2>取得できなかった記事</h2>{''.join(failed_cards)}</section>'''
        html = f'''<!doctype html><html lang="ja"><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="margin:0;background:#f3f2ec;color:#303730;font-family:-apple-system,BlinkMacSystemFont,'Hiragino Kaku Gothic ProN',sans-serif">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center" style="padding:24px 12px"><table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#fffdf8"><tr><td style="padding:28px 24px">
<header style="border-top:3px solid {accent};border-bottom:1px solid #deded5;padding:20px 0;margin-bottom:28px">
{title_heading}
<p style="margin:0;font-size:12px;letter-spacing:1px;color:#777c78">{escape(day)} · {len(ordered)} articles</p></header>
{''.join(cards)}{failure_section}<footer style="padding-top:8px;font-size:12px;color:#969b92">Read less. Learn more.</footer>
</td></tr></table></td></tr></table></body></html>'''
        return Digest(execution_date=day, results=tuple(ordered), html_content=html,
                      failed_results=tuple(failures))
