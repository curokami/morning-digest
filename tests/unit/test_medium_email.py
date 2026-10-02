from morning_digest.collectors.medium_email import (
    EmailMetadata,
    find_medium_daily_digest_files,
    is_medium_daily_digest,
    read_email_metadata,
)


def write_email(path, sender, subject):
    path.write_text(
        f"From: {sender}\n"
        "To: reader@example.com\n"
        f"Subject: {subject}\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Email body.\n",
        encoding="utf-8",
    )


def test_reads_subject_and_sender_from_eml(tmp_path):
    email_path = tmp_path / "medium-daily-digest.eml"
    email_path.write_text(
        "From: Medium Daily Digest <noreply@medium.com>\n"
        "To: reader@example.com\n"
        "Subject: Medium Daily Digest\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Today's recommendations.\n",
        encoding="utf-8",
    )

    metadata = read_email_metadata(email_path)

    assert metadata.subject == "Medium Daily Digest"
    assert metadata.sender == "Medium Daily Digest <noreply@medium.com>"


def test_identifies_medium_daily_digest_with_a_variable_subject():
    metadata = EmailMetadata(
        subject="How Senior Engineers Make Reliable Systems",
        sender="Medium Daily Digest <noreply@medium.com>",
    )

    assert is_medium_daily_digest(metadata)


def test_rejects_other_medium_email():
    metadata = EmailMetadata(
        subject="New response to your story",
        sender="Medium <noreply@medium.com>",
    )

    assert not is_medium_daily_digest(metadata)


def test_rejects_daily_digest_name_from_another_domain():
    metadata = EmailMetadata(
        subject="Today's recommendations",
        sender="Medium Daily Digest <newsletter@example.com>",
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
