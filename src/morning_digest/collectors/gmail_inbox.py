from __future__ import annotations

import imaplib
from collections.abc import Callable
from typing import Any

from morning_digest.collectors.medium_email import (
    ParsedEmail,
    is_medium_daily_digest,
    parse_email_message,
)


class GmailInboxError(RuntimeError):
    """Raised when Gmail cannot provide a requested inbox message."""


class GmailInboxReader:
    def __init__(
        self,
        username: str,
        app_password: str,
        client_factory: Callable[[str], Any] = imaplib.IMAP4_SSL,
    ) -> None:
        self.username = username
        self.app_password = app_password
        self.client_factory = client_factory

    def read_latest_medium_daily_digest(self) -> ParsedEmail | None:
        """Fetch, parse, and validate the latest Medium Daily Digest."""
        raw_message = self.fetch_latest_medium_daily_digest()
        if raw_message is None:
            return None

        try:
            parsed_email = parse_email_message(raw_message)
        except ValueError as error:
            raise GmailInboxError("Gmail returned an unreadable email") from error

        if not is_medium_daily_digest(parsed_email.metadata):
            raise GmailInboxError(
                "Gmail search returned an email from an unexpected sender"
            )
        return parsed_email

    def fetch_latest_medium_daily_digest(self) -> bytes | None:
        """Fetch the latest matching message without changing its read state."""
        client = self.client_factory("imap.gmail.com")
        try:
            status, _ = client.login(self.username, self.app_password)
            self._require_ok(status, "authenticate with Gmail")

            status, _ = client.select("INBOX", readonly=True)
            self._require_ok(status, "open Gmail INBOX read-only")

            status, search_data = client.uid(
                "search",
                None,
                "HEADER",
                "FROM",
                '"Medium Daily Digest <noreply@medium.com>"',
            )
            self._require_ok(status, "search for Medium Daily Digest")
            message_uids = search_data[0].split() if search_data else []
            if not message_uids:
                return None

            status, fetch_data = client.uid(
                "fetch", message_uids[-1], "(BODY.PEEK[])"
            )
            self._require_ok(status, "fetch Medium Daily Digest")
            for response_part in fetch_data:
                if (
                    isinstance(response_part, tuple)
                    and len(response_part) >= 2
                    and isinstance(response_part[1], bytes)
                ):
                    return response_part[1]
            raise GmailInboxError("Gmail returned no message body")
        finally:
            client.logout()

    @staticmethod
    def _require_ok(status: str, operation: str) -> None:
        if status != "OK":
            raise GmailInboxError(f"Could not {operation}")
