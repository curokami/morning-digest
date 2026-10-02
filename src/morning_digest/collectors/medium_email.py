from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path


@dataclass(frozen=True)
class EmailMetadata:
    subject: str
    sender: str
    sent_at: datetime


@dataclass(frozen=True)
class EmailBody:
    content_type: str
    content: str


@dataclass(frozen=True)
class MediumDailyDigestEmail:
    source_path: Path
    metadata: EmailMetadata
    body: EmailBody


def is_medium_daily_digest(metadata: EmailMetadata) -> bool:
    """Return whether the sender identifies a Medium Daily Digest email."""
    sender_name, sender_address = parseaddr(metadata.sender)
    return (
        sender_name.strip().casefold() == "medium daily digest"
        and sender_address.casefold() == "noreply@medium.com"
    )


def find_medium_daily_digest_files(email_paths: Iterable[Path]) -> list[Path]:
    """Return EML files identified as Medium Daily Digest emails."""
    return [
        email_path
        for email_path in email_paths
        if is_medium_daily_digest(read_email_metadata(email_path))
    ]


def find_latest_medium_daily_digest_file(
    email_paths: Iterable[Path],
) -> Path | None:
    """Return the most recently sent Medium Daily Digest EML file, if any."""
    digest_files = find_medium_daily_digest_files(email_paths)
    return max(
        digest_files,
        key=lambda email_path: read_email_metadata(email_path).sent_at,
        default=None,
    )


def read_preferred_email_body(email_path: Path) -> EmailBody:
    """Read an email's HTML body, falling back to its plain-text body."""
    with email_path.open("rb") as email_file:
        message = BytesParser(policy=policy.default).parse(email_file)

    body_part = message.get_body(preferencelist=("html", "plain"))
    if body_part is None:
        raise ValueError("Email requires an HTML or plain-text body")

    content = body_part.get_content()
    if not isinstance(content, str):
        raise ValueError("Email text body could not be decoded")

    return EmailBody(content_type=body_part.get_content_type(), content=content)


def read_latest_medium_daily_digest(
    email_paths: Iterable[Path],
) -> MediumDailyDigestEmail | None:
    """Find and read the latest Medium Daily Digest EML file."""
    source_path = find_latest_medium_daily_digest_file(email_paths)
    if source_path is None:
        return None

    return MediumDailyDigestEmail(
        source_path=source_path,
        metadata=read_email_metadata(source_path),
        body=read_preferred_email_body(source_path),
    )


def read_email_metadata(email_path: Path) -> EmailMetadata:
    """Read the identifying headers from an RFC 5322 email file."""
    with email_path.open("rb") as email_file:
        message = BytesParser(policy=policy.default).parse(email_file, headersonly=True)

    subject = message.get("Subject")
    sender = message.get("From")
    date = message.get("Date")
    if subject is None or sender is None or date is None:
        raise ValueError("Email requires Subject, From, and Date headers")

    try:
        sent_at = parsedate_to_datetime(str(date))
    except (TypeError, ValueError) as error:
        raise ValueError("Email Date header must be valid") from error
    if sent_at is None or sent_at.tzinfo is None:
        raise ValueError("Email Date header must include a timezone")

    return EmailMetadata(subject=str(subject), sender=str(sender), sent_at=sent_at)
