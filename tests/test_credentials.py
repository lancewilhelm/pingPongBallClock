import base64
import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from test_api import api, storage
import credentials


class CredentialsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = pathlib.Path(self.temp.name)
        self.path = self.directory / "auth.json"
        self.path.write_text(json.dumps({"username": "admin", "password": "old-secret"}))
        patcher = patch.object(storage, "STATE_DIR", self.directory)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = api.app.test_client()

    def sign_in(self, username, password):
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        return self.client.get("/api/state", headers={"Authorization": "Basic " + token}).status_code

    def reset(self, username, passwords):
        output, errors = io.StringIO(), io.StringIO()
        with patch("builtins.input", return_value=username), patch("getpass.getpass", side_effect=passwords):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                result = credentials.main()
        return result, output.getvalue(), errors.getvalue()

    def test_password_change_applies_immediately_and_stays_private(self):
        self.assertEqual(self.sign_in("admin", "old-secret"), 200)
        result, output, _ = self.reset("", ["new-secret", "new-secret"])
        self.assertEqual(result, 0)
        self.assertNotIn("new-secret", output)
        self.assertEqual(self.sign_in("admin", "old-secret"), 401)
        self.assertEqual(self.sign_in("admin", "new-secret"), 200)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_username_can_be_changed(self):
        result, _, _ = self.reset("clock-owner", ["new-secret", "new-secret"])
        self.assertEqual(result, 0)
        self.assertEqual(self.sign_in("clock-owner", "new-secret"), 200)
        self.assertEqual(self.sign_in("admin", "new-secret"), 401)

    def test_mismatch_and_invalid_username_preserve_existing_login(self):
        self.assertEqual(self.reset("", ["one", "two"])[0], 1)
        self.assertEqual(self.reset("bad:name", [])[0], 1)
        self.assertEqual(self.sign_in("admin", "old-secret"), 200)

    def test_missing_credentials_can_be_recovered(self):
        self.path.unlink()
        self.assertEqual(self.reset("", ["new-secret", "new-secret"])[0], 0)
        self.assertEqual(self.sign_in("admin", "new-secret"), 200)


if __name__ == "__main__":
    unittest.main()
