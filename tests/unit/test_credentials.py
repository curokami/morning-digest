import os
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from morning_digest.credentials import load_credentials


def test_environment_value_takes_precedence_over_keychain():
    with patch.dict(os.environ, {"TOKEN": "from-environment"}, clear=True), \
            patch("morning_digest.credentials._macos_keychain_value") as keychain:
        assert load_credentials(["TOKEN"]) == {"TOKEN": "from-environment"}
    keychain.assert_not_called()


def test_macos_keychain_value_is_loaded_into_runtime_environment():
    completed = CompletedProcess([], 0, stdout="from-keychain\n", stderr="")
    with patch.dict(os.environ, {}, clear=True), \
            patch("morning_digest.credentials.sys.platform", "darwin"), \
            patch("morning_digest.credentials.subprocess.run", return_value=completed) as run:
        assert load_credentials(["TOKEN"]) == {"TOKEN": "from-keychain"}
        assert os.environ["TOKEN"] == "from-keychain"
    command = run.call_args.args[0]
    assert command == ["/usr/bin/security", "find-generic-password", "-a",
                       "morning-digest", "-s", "TOKEN", "-w"]


def test_missing_credential_names_are_reported_without_values():
    with patch.dict(os.environ, {}, clear=True), \
            patch("morning_digest.credentials._macos_keychain_value", return_value=None):
        with pytest.raises(RuntimeError, match="MISSING_ONE, MISSING_TWO"):
            load_credentials(["MISSING_ONE", "MISSING_TWO"])
