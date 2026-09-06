from __future__ import annotations

import json

from openai import OpenAI

from morning_digest.domain import Article, ProcessingResult, ReadingPriority, Recommendation, Summary
from morning_digest.taxonomy import Taxonomy


class OpenAIProcessor:
    def __init__(self, model: str, taxonomy: Taxonomy, client: OpenAI | None = None) -> None:
        self.model = model
        self.taxonomy = taxonomy
        self.client = client or OpenAI()

    def process(self, article: Article) -> ProcessingResult:
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "あなたは個人向け記事選別アシスタントです。人気ではなく、今読む価値を判断してください。"
                "要約は日本語3〜5文、読む理由は日本語1〜2文。優先度は関連性40%、新規性20%、"
                "影響度20%、実行可能性20%で1〜5。タグは指定候補だけを使い、該当なしはUncategorized。"
            ),
            input=json.dumps({
                "title": article.title, "author": article.author,
                "publication_date": article.publication_date,
                "source_tags": article.source_tags, "content": article.content[:30000],
                "controlled_tags": sorted(self.taxonomy.tags),
            }, ensure_ascii=False),
            text={"format": {"type": "json_schema", "name": "article_assessment", "strict": True,
                "schema": {"type": "object", "additionalProperties": False,
                    "properties": {
                        "summary": {"type": "string"},
                        "reading_priority": {"type": "integer", "minimum": 1, "maximum": 5},
                        "reason_to_read": {"type": "string"},
                        "digest_tags": {
                            "type": "array",
                            "items": {"type": "string", "enum": sorted(self.taxonomy.tags)},
                            "minItems": 1,
                            "maxItems": 3,
                        },
                    }, "required": ["summary", "reading_priority", "reason_to_read", "digest_tags"]}}},
        )
        data = json.loads(response.output_text)
        tags = self.taxonomy.validate(data["digest_tags"])
        if not data["summary"].strip() or not data["reason_to_read"].strip():
            raise ValueError("AI returned an empty required field")
        return ProcessingResult(
            article=article, status="success",
            summary=Summary(language="ja", text=data["summary"].strip()),
            recommendation=Recommendation(
                reading_priority=ReadingPriority(data["reading_priority"]),
                reason_to_read=data["reason_to_read"].strip(), digest_tags=tags,
            ),
        )
