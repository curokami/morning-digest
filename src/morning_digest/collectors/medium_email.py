from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from pathlib import Path


@dataclass(frozen=True)
class EmailMetadata:
    subject: str
    sender: str


def is_medium_daily_digest(metadata: EmailMetadata) -> bool:
    """Return whether the sender identifies a Medium Daily Digest email."""
    sender_name, sender_address = parseaddr(metadata.sender)
    return (
        sender_name.strip().casefold() == "medium daily digest"
        and sender_address.casefold() == "noreply@medium.com"
    )


def read_email_metadata(email_path: Path) -> EmailMetadata:
    """Read the identifying headers from an RFC 5322 email file."""
    with email_path.open("rb") as email_file:
        message = BytesParser(policy=policy.default).parse(email_file, headersonly=True)

    subject = message.get("Subject")
    sender = message.get("From")
    if subject is None or sender is None:
        raise ValueError("Email requires Subject and From headers")

    return EmailMetadata(subject=str(subject), sender=str(sender))
