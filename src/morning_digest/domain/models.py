from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class ReadingPriority(IntEnum):
    LOW = 1
    OPTIONAL = 2
    WORTH_READING = 3
    HIGH = 4
    READ_TODAY = 5

    @property
    def label(self) -> str:
        return {1: "Low Priority", 2: "Optional", 3: "Worth Reading",
                4: "High Priority", 5: "Read Today"}[self.value]


@dataclass(frozen=True)
class Article:
    title: str
    canonical_url: str
    source: str
    author: str | None = None
    publication_date: str | None = None
    source_tags: tuple[str, ...] = ()
    content: str = ""
    preference_weight: float = 1.0

    def __post_init__(self) -> None:
        if self.preference_weight <= 0:
            raise ValueError("Article preference weight must be greater than zero")


@dataclass(frozen=True)
class Summary:
    language: str
    text: str


@dataclass(frozen=True)
class Recommendation:
    reading_priority: ReadingPriority
    reason_to_read: str
    digest_tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.digest_tags:
            raise ValueError("A recommendation requires at least one Digest Tag")


@dataclass(frozen=True)
class ProcessingResult:
    article: Article
    status: str
    summary: Summary | None = None
    recommendation: Recommendation | None = None
    error: str | None = None
    processed_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())


@dataclass(frozen=True)
class Digest:
    execution_date: str
    results: tuple[ProcessingResult, ...]
    html_content: str


@dataclass(frozen=True)
class DeliveryResult:
    status: str
    provider_message_id: str | None = None
    error: str | None = None
