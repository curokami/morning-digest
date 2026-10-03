from morning_digest.collectors.gmail_inbox import GmailInboxReader


class FakeImapClient:
    def __init__(self, search_result=b"101 205", message=b"raw email"):
        self.search_result = search_result
        self.message = message
        self.calls = []

    def login(self, username, app_password):
        self.calls.append(("login", username, app_password))
        return "OK", [b"authenticated"]

    def select(self, mailbox, readonly=False):
        self.calls.append(("select", mailbox, readonly))
        return "OK", [b"2"]

    def uid(self, command, *arguments):
        self.calls.append(("uid", command, *arguments))
        if command == "search":
            return "OK", [self.search_result]
        if command == "fetch":
            return "OK", [(b"205 (BODY[] {9}", self.message), b")"]
        raise AssertionError(f"Unexpected UID command: {command}")

    def logout(self):
        self.calls.append(("logout",))
        return "BYE", [b"logout"]


def test_fetches_latest_medium_daily_digest_without_marking_it_read():
    client = FakeImapClient(message=b"latest Medium Daily Digest")
    hosts = []
    reader = GmailInboxReader(
        "reader@gmail.com",
        "app-password",
        client_factory=lambda host: hosts.append(host) or client,
    )

    message = reader.fetch_latest_medium_daily_digest()

    assert message == b"latest Medium Daily Digest"
    assert hosts == ["imap.gmail.com"]
    assert ("select", "INBOX", True) in client.calls
    assert (
        "uid",
        "search",
        None,
        "HEADER",
        "FROM",
        '"Medium Daily Digest <noreply@medium.com>"',
    ) in client.calls
    assert ("uid", "fetch", b"205", "(BODY.PEEK[])") in client.calls
    assert client.calls[-1] == ("logout",)


def test_returns_none_when_inbox_has_no_medium_daily_digest():
    client = FakeImapClient(search_result=b"")
    reader = GmailInboxReader(
        "reader@gmail.com",
        "app-password",
        client_factory=lambda _host: client,
    )

    assert reader.fetch_latest_medium_daily_digest() is None
    assert not any(call[:2] == ("uid", "fetch") for call in client.calls)
    assert client.calls[-1] == ("logout",)
