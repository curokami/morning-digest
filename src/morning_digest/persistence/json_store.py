from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from morning_digest.domain import Article, ProcessingResult, ReadingPriority, Recommendation, Summary


class JsonStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"articles": {}, "pending_delivery": []}
        with self.path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        data.setdefault("articles", {})
        data.setdefault("pending_delivery", [])
        return data

    def is_successful(self, canonical_url: str) -> bool:
        return self.data["articles"].get(canonical_url, {}).get("status") == "success"

    def save_result(self, result: ProcessingResult) -> None:
        record = self._serialize(result)
        self.data["articles"][result.article.canonical_url] = record
        if result.status == "success" and result.article.canonical_url not in self.data["pending_delivery"]:
            self.data["pending_delivery"].append(result.article.canonical_url)
        self._flush()

    def pending_results(self) -> list[ProcessingResult]:
        return [self._deserialize(self.data["articles"][url])
                for url in self.data["pending_delivery"] if url in self.data["articles"]]

    def mark_delivered(self, urls: list[str]) -> None:
        delivered = set(urls)
        self.data["pending_delivery"] = [url for url in self.data["pending_delivery"] if url not in delivered]
        self._flush()

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=f".{self.path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(self.data, stream, ensure_ascii=False, indent=2)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _serialize(result: ProcessingResult) -> dict:
        article = result.article
        record = {"status": result.status, "processed_at": result.processed_at, "error": result.error,
            "article": {"title": article.title, "canonical_url": article.canonical_url,
                "source": article.source, "author": article.author, "publication_date": article.publication_date,
                "source_tags": list(article.source_tags), "content": article.content,
                "preference_weight": article.preference_weight}}
        if result.summary:
            record["summary"] = {"language": result.summary.language, "text": result.summary.text}
        if result.recommendation:
            record["recommendation"] = {"reading_priority": int(result.recommendation.reading_priority),
                "reason_to_read": result.recommendation.reason_to_read,
                "digest_tags": list(result.recommendation.digest_tags)}
        return record

    @staticmethod
    def _deserialize(record: dict) -> ProcessingResult:
        article_data = record["article"].copy()
        article_data["source_tags"] = tuple(article_data.get("source_tags", []))
        article = Article(**article_data)
        summary_data = record.get("summary")
        recommendation_data = record.get("recommendation")
        return ProcessingResult(article=article, status=record["status"], error=record.get("error"),
            processed_at=record["processed_at"],
            summary=Summary(**summary_data) if summary_data else None,
            recommendation=Recommendation(
                reading_priority=ReadingPriority(recommendation_data["reading_priority"]),
                reason_to_read=recommendation_data["reason_to_read"],
                digest_tags=tuple(recommendation_data["digest_tags"])) if recommendation_data else None)
