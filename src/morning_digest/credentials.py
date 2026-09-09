from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterable


KEYCHAIN_ACCOUNT = "morning-digest"


def load_credentials(names: Iterable[str]) -> dict[str, str]:
    """Load credentials from the environment, then the macOS Keychain."""
    credentials: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        value = os.getenv(name) or _macos_keychain_value(name)
        if value:
            credentials[name] = value
            os.environ.setdefault(name, value)
        else:
            missing.append(name)
    if missing:
        raise RuntimeError(
            "Missing required credentials in environment variables or macOS Keychain: "
            + ", ".join(missing)
        )
    return credentials


def _macos_keychain_value(service: str) -> str | None:
    if sys.platform != "darwin":
        return None
    result = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-a", KEYCHAIN_ACCOUNT,
         "-s", service, "-w"],
        capture_output=True,
        text=True,
        check=False,
    )
    value = result.stdout.rstrip("\r\n")
    return value if result.returncode == 0 and value else None
