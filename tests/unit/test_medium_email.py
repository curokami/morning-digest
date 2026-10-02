from datetime import datetime
from email.message import EmailMessage

import pytest

from morning_digest.collectors.medium_email import (
    EmailBody,
    EmailMetadata,
    find_medium_daily_digest_files,
    find_latest_medium_daily_digest_file,
    is_medium_daily_digest,
    read_preferred_email_body,
    read_email_metadata,
)

SENT_AT = datetime.fromisoformat("2026-10-02T07:30:00+09:00")


def write_email(path, sender, subject, date="Fri, 02 Oct 2026 07:30:00 +0900"):
    path.write_text(
        f"From: {sender}\n"
        "To: reader@example.com\n"
        f"Subject: {subject}\n"
        f"Date: {date}\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Email body.\n",
        encoding="utf-8",
    )


def test_reads_identifying_metadata_from_eml(tmp_path):
    email_path = tmp_path / "medium-daily-digest.eml"
    email_path.write_text(
        "From: Medium Daily Digest <noreply@medium.com>\n"
        "To: reader@example.com\n"
        "Subject: Medium Daily Digest\n"
        "Date: Fri, 02 Oct 2026 07:30:00 +0900\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Today's recommendations.\n",
        encoding="utf-8",
    )

    metadata = read_email_metadata(email_path)

    assert metadata.subject == "Medium Daily Digest"
    assert metadata.sender == "Medium Daily Digest <noreply@medium.com>"
    assert metadata.sent_at == SENT_AT


def test_rejects_eml_without_date_header(tmp_path):
    email_path = tmp_path / "missing-date.eml"
    email_path.write_text(
        "From: Medium Daily Digest <noreply@medium.com>\n"
        "Subject: Recommendations\n"
        "\n"
        "Email body.\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Subject, From, and Date"):
        read_email_metadata(email_path)


def test_identifies_medium_daily_digest_with_a_variable_subject():
    metadata = EmailMetadata(
        subject="How Senior Engineers Make Reliable Systems",
        sender="Medium Daily Digest <noreply@medium.com>",
        sent_at=SENT_AT,
    )

    assert is_medium_daily_digest(metadata)


def test_rejects_other_medium_email():
    metadata = EmailMetadata(
        subject="New response to your story",
        sender="Medium <noreply@medium.com>",
        sent_at=SENT_AT,
    )

    assert not is_medium_daily_digest(metadata)


def test_rejects_daily_digest_name_from_another_domain():
    metadata = EmailMetadata(
        subject="Today's recommendations",
        sender="Medium Daily Digest <newsletter@example.com>",
        sent_at=SENT_AT,
    )

    assert not is_medium_daily_digest(metadata)


def test_finds_only_medium_daily_digest_files_and_preserves_order(tmp_path):
    first_digest = tmp_path / "first-digest.eml"
    medium_notification = tmp_path / "medium-notification.eml"
    unrelated_email = tmp_path / "unrelated.eml"
    second_digest = tmp_path / "second-digest.eml"
    write_email(
        first_digest,
        "Medium Daily Digest <noreply@medium.com>",
        "First recommendations",
    )
    write_email(
        medium_notification,
        "Medium <noreply@medium.com>",
        "Someone responded to your story",
    )
    write_email(
        unrelated_email,
        "Python Weekly <newsletter@pythonweekly.com>",
        "Python Weekly Issue 765",
    )
    write_email(
        second_digest,
        "Medium Daily Digest <noreply@medium.com>",
        "Second recommendations",
    )

    matches = find_medium_daily_digest_files(
        [first_digest, medium_notification, unrelated_email, second_digest]
    )

    assert matches == [first_digest, second_digest]


def test_finds_latest_medium_daily_digest_file(tmp_path):
    older_digest = tmp_path / "older-digest.eml"
    latest_digest = tmp_path / "latest-digest.eml"
    newer_unrelated_email = tmp_path / "newer-unrelated.eml"
    write_email(
        older_digest,
        "Medium Daily Digest <noreply@medium.com>",
        "Older recommendations",
        "Thu, 01 Oct 2026 07:30:00 +0900",
    )
    write_email(
        latest_digest,
        "Medium Daily Digest <noreply@medium.com>",
        "Latest recommendations",
        "Fri, 02 Oct 2026 07:30:00 +0900",
    )
    write_email(
        newer_unrelated_email,
        "Python Weekly <newsletter@pythonweekly.com>",
        "Python Weekly Issue 765",
        "Sat, 03 Oct 2026 07:30:00 +0900",
    )

    latest = find_latest_medium_daily_digest_file(
        [older_digest, newer_unrelated_email, latest_digest]
    )

    assert latest == latest_digest


def test_latest_medium_daily_digest_is_none_when_no_digest_exists(tmp_path):
    unrelated_email = tmp_path / "unrelated.eml"
    write_email(
        unrelated_email,
        "Python Weekly <newsletter@pythonweekly.com>",
        "Python Weekly Issue 765",
    )

    assert find_latest_medium_daily_digest_file([unrelated_email]) is None


def test_reads_html_body_from_multipart_alternative(tmp_path):
    email_path = tmp_path / "html-digest.eml"
    message = EmailMessage()
    message.set_content("Plain recommendations")
    message.add_alternative(
        "<html><body><h1>Rich recommendations</h1></body></html>",
        subtype="html",
    )
    email_path.write_bytes(message.as_bytes())

    body = read_preferred_email_body(email_path)

    assert body == EmailBody(
        content_type="text/html",
        content="<html><body><h1>Rich recommendations</h1></body></html>\n",
    )


def test_falls_back_to_plain_body_and_ignores_html_attachment(tmp_path):
    email_path = tmp_path / "plain-digest.eml"
    message = EmailMessage()
    message.set_content("Plain recommendations")
    message.add_attachment(
        "<html><body>Attached document</body></html>",
        subtype="html",
        filename="attached.html",
    )
    email_path.write_bytes(message.as_bytes())

    body = read_preferred_email_body(email_path)

    assert body == EmailBody(
        content_type="text/plain",
        content="Plain recommendations\n",
    )
