"""Contract tests for JSON loading, validation, and safe replacement."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from alert_manager.models import Alert
from alert_manager.service import PersistenceError
from alert_manager.storage import JsonAlertStore

VALID_RECORD = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Suspicious login",
    "description": "Repeated failed login attempts.",
    "source_ip": "203.0.113.7",
    "severity": "High",
    "status": "New",
    "created_at": "2026-11-04T12:30:45Z",
}


def make_alert(**changes: str) -> Alert:
    return Alert.from_dict(dict(VALID_RECORD, **changes))


def store_bytes(alerts: list[dict[str, str]]) -> bytes:
    return json.dumps({"alerts": alerts}, separators=(",", ":")).encode("utf-8")


class JsonAlertStoreContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.path = self.directory / "alerts.json"
        self.store = JsonAlertStore(self.path)
        if os.name == "nt":
            environment = os.environ.copy()
            environment["ALERT_TEST_DIRECTORY"] = str(self.directory)
            restrict_acl = (
                "$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name; "
                "& icacls.exe $env:ALERT_TEST_DIRECTORY /inheritance:r /grant:r "
                "\"$identity`:(OI)(CI)F\" | Out-Null; exit $LASTEXITCODE"
            )
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", restrict_acl],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_round_trip_and_missing_file(self) -> None:
        self.assertEqual(self.store.load(), [])
        self.assertFalse(self.path.exists())
        alert = make_alert()
        self.store.save([alert])
        self.assertEqual(self.store.load(), [alert])

    def test_malformed_json_fails_closed_and_preserves_bytes(self) -> None:
        original = b'{"alerts": [not-json]}'
        self.path.write_bytes(original)
        with self.assertRaises(PersistenceError):
            self.store.load()
        self.assertEqual(self.path.read_bytes(), original)

    def test_invalid_store_shapes_fail_closed_and_preserve_bytes(self) -> None:
        invalid_documents = (
            b"[]",
            b'{"alerts":{}}',
            b'{"alerts":[],"extra":true}',
            store_bytes([dict(VALID_RECORD, unexpected="field")]),
            store_bytes([dict(VALID_RECORD, source_ip="hostname.invalid")]),
        )
        for original in invalid_documents:
            with self.subTest(document=original[:32]):
                self.path.write_bytes(original)
                with self.assertRaises(PersistenceError):
                    self.store.load()
                self.assertEqual(self.path.read_bytes(), original)

    def test_duplicate_alert_ids_fail_closed_and_preserve_bytes(self) -> None:
        original = store_bytes([VALID_RECORD, dict(VALID_RECORD, title="Second")])
        self.path.write_bytes(original)
        with self.assertRaises(PersistenceError):
            self.store.load()
        self.assertEqual(self.path.read_bytes(), original)

    def test_duplicate_json_object_keys_fail_and_preserve_raw_fixture(self) -> None:
        fixture = Path(__file__).parents[1] / "fixtures" / "duplicate-json-keys.json"
        original = fixture.read_bytes()
        self.path.write_bytes(original)
        with self.assertRaises(PersistenceError):
            self.store.load()
        self.assertEqual(self.path.read_bytes(), original)

    def test_oversized_file_is_rejected_before_reading(self) -> None:
        with patch.object(Path, "stat", return_value=SimpleNamespace(st_size=256 * 1024 * 1024 + 1)), \
                self.assertRaises(PersistenceError):
            self.store.load()

    def test_unreadable_file_fails_closed(self) -> None:
        self.path.write_bytes(store_bytes([VALID_RECORD]))
        with patch.object(Path, "open", side_effect=PermissionError("denied")), \
                self.assertRaises(PersistenceError):
            self.store.load()

    def test_failed_replace_preserves_target_bytes_and_cleans_temporary_file(self) -> None:
        original = store_bytes([VALID_RECORD])
        self.path.write_bytes(original)
        updated = make_alert(title="Updated")
        with patch("alert_manager.storage.os.replace", side_effect=OSError("replace denied")), \
                self.assertRaises(PersistenceError):
            self.store.save([updated])
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.directory.glob(".alerts.json.*.tmp")), [])

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not available on Windows")
    def test_created_and_replaced_files_have_user_only_permissions(self) -> None:
        alert = make_alert()
        self.store.save([alert])
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.store.save([])
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)

    @unittest.skipUnless(os.name == "nt", "Windows inherited ACL check")
    def test_created_file_inherits_parent_acl(self) -> None:
        self.store.save([make_alert()])
        command = "(Get-Acl -LiteralPath $env:ALERT_TEST_ACL_PATH).AccessToString"
        environment = os.environ.copy()
        environment["ALERT_TEST_ACL_PATH"] = str(self.directory)
        parent_acl = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        ).stdout.strip()
        environment["ALERT_TEST_ACL_PATH"] = str(self.path)
        file_acl = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        ).stdout.strip()
        self.assertEqual(len(parent_acl.splitlines()), 1)
        self.assertEqual(len(file_acl.splitlines()), 1)
        self.assertIn("FullControl", file_acl)
        self.assertEqual(file_acl, parent_acl)


if __name__ == "__main__":
    unittest.main()
