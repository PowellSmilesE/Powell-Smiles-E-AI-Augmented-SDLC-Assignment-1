"""Subprocess contract tests for command parsing and observable behavior."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from alert_manager.cli import main as cli_main
from alert_manager.storage import JsonAlertStore


class CliContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.store = self.directory / "alerts.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        source_root = str(Path(__file__).parents[2] / "src")
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = source_root if not existing else source_root + os.pathsep + existing
        return subprocess.run(
            [sys.executable, "-m", "alert_manager", "--store", str(self.store), *arguments],
            capture_output=True,
            input="",
            text=True,
            env=environment,
            timeout=10,
            check=False,
        )

    def create_alert(
        self, title: str, severity: str = "High", source_ip: str = "203.0.113.7"
    ) -> dict[str, str]:
        result = self.invoke(
            "create", "--title", title, "--description", f"Details for {title}",
            "--source-ip", source_ip, "--severity", severity,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["alert"]

    def test_create_list_get_persist_across_processes(self) -> None:
        created = self.invoke(
            "create", "--title", "Suspicious login", "--description", "Repeated failed attempts",
            "--source-ip", "203.0.113.7", "--severity", "High",
        )
        self.assertEqual(created.returncode, 0, created.stderr)
        record = json.loads(created.stdout)
        alert = record["alert"]
        self.assertEqual(alert["status"], "New")
        self.assertTrue(alert["created_at"].endswith("Z"))

        listed = self.invoke("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(json.loads(listed.stdout), [alert])

        retrieved = self.invoke("get", alert["id"])
        self.assertEqual(retrieved.returncode, 0, retrieved.stderr)
        self.assertEqual(json.loads(retrieved.stdout), alert)

    def test_exit_codes_for_success_usage_invalid_not_found_and_persistence(self) -> None:
        self.assertEqual(self.invoke("--help").returncode, 0)
        self.assertEqual(self.invoke().returncode, 2)
        invalid = self.invoke("create", "--title", "Title", "--description", "Description",
                              "--source-ip", "203.0.113.7", "--severity", "Urgent")
        self.assertEqual(invalid.returncode, 3)
        missing = self.invoke("get", "550e8400-e29b-41d4-a716-446655440001")
        self.assertEqual(missing.returncode, 4)

        self.store = self.directory / "absent" / "alerts.json"
        failed_write = self.invoke("create", "--title", "Title", "--description", "Description",
                                   "--source-ip", "203.0.113.7", "--severity", "High")
        self.assertEqual(failed_write.returncode, 5)
        self.assertNotIn("Alert created", failed_write.stdout)

    def test_combined_search_optional_filters_and_uuid_order(self) -> None:
        first = self.create_alert("Suspicious alpha", "High")
        second = self.create_alert("Suspicious malware", "Critical")
        third = self.create_alert("Network alpha", "High")

        all_text = self.invoke("search", "suspicious")
        self.assertEqual(all_text.returncode, 0, all_text.stderr)
        all_matches = json.loads(all_text.stdout)
        self.assertEqual({item["id"] for item in all_matches}, {first["id"], second["id"]})
        self.assertEqual([UUID(item["id"]).int for item in all_matches],
                         sorted(UUID(item["id"]).int for item in all_matches))

        severity_only = self.invoke("search", "suspicious", "--severity", "High")
        self.assertEqual([a["id"] for a in json.loads(severity_only.stdout)], [first["id"]])
        status_only = self.invoke("search", "suspicious", "--status", "New")
        self.assertEqual({a["id"] for a in json.loads(status_only.stdout)}, {first["id"], second["id"]})
        combined = self.invoke("search", "suspicious", "--severity", "High", "--status", "New")
        self.assertEqual([a["id"] for a in json.loads(combined.stdout)], [first["id"]])
        no_match = self.invoke("search", "missing phrase", "--severity", "High")
        self.assertEqual(json.loads(no_match.stdout), [])
        standalone_filter = self.invoke("filter", "--severity", "High", "--status", "New")
        self.assertEqual({a["id"] for a in json.loads(standalone_filter.stdout)},
                         {first["id"], third["id"]})

    def test_updates_and_status_persist_across_fresh_processes(self) -> None:
        created = self.create_alert("Original", "High")
        original_bytes = self.store.read_bytes()
        original_id = created["id"]
        original_timestamp = created["created_at"]

        result = self.invoke("update", original_id, "--title", "Changed", "--description", "Changed details",
                             "--source-ip", "2001:db8::7", "--severity", "Low")
        self.assertEqual(result.returncode, 0, result.stderr)
        reopened = self.invoke("get", original_id)
        self.assertEqual(reopened.returncode, 0, reopened.stderr)
        record = json.loads(reopened.stdout)
        self.assertEqual(record["title"], "Changed")
        self.assertEqual(record["severity"], "Low")
        self.assertEqual(record["id"], original_id)
        self.assertEqual(record["created_at"], original_timestamp)
        self.assertNotEqual(self.store.read_bytes(), original_bytes)

        changed_status = self.invoke("status", original_id, "Resolved")
        self.assertEqual(changed_status.returncode, 0, changed_status.stderr)
        reopened_again = self.invoke("get", original_id)
        persisted = json.loads(reopened_again.stdout)
        self.assertEqual(persisted["status"], "Resolved")
        self.assertEqual(persisted["id"], original_id)
        self.assertEqual(persisted["created_at"], original_timestamp)

    def test_rejected_mutations_return_errors_and_preserve_store_bytes(self) -> None:
        alert = self.create_alert("Unchanged")
        rejected_commands = (
            ("update", alert["id"], "--title", "  "),
            ("update", alert["id"], "--title", "x" * 201),
            ("update", alert["id"], "--description", ""),
            ("update", alert["id"], "--description", "x" * 4001),
            ("update", alert["id"], "--source-ip", "host.invalid"),
            ("update", alert["id"], "--severity", "Urgent"),
            ("status", alert["id"], "Waiting"),
            ("update", "550e8400-e29b-41d4-a716-446655440099", "--title", "Unknown"),
            ("status", "550e8400-e29b-41d4-a716-446655440099", "Closed"),
            ("delete", "550e8400-e29b-41d4-a716-446655440099", "--yes"),
        )
        for command in rejected_commands:
            with self.subTest(command=command):
                before = self.store.read_bytes()
                result = self.invoke(*command)
                self.assertIn(result.returncode, (3, 4), result.stderr)
                self.assertTrue(result.stderr.strip(), command)
                self.assertEqual(self.store.read_bytes(), before)

        unknown_field = self.invoke("update", alert["id"], "--priority", "Critical")
        self.assertEqual(unknown_field.returncode, 2)
        self.assertTrue(unknown_field.stderr.strip())

    def test_delete_confirmation_and_restart_persistence(self) -> None:
        alert = self.create_alert("To delete")
        confirmed = self.invoke("delete", alert["id"], "--yes")
        self.assertEqual(confirmed.returncode, 0, confirmed.stderr)
        self.assertTrue(json.loads(confirmed.stdout)["deleted"])
        after_confirmation = self.invoke("get", alert["id"])
        self.assertEqual(after_confirmation.returncode, 4)

        retained = self.create_alert("Keep this alert")
        before = self.store.read_bytes()

        class InteractiveInput(io.StringIO):
            def isatty(self) -> bool:
                return True

        output = io.StringIO()
        errors = io.StringIO()
        with patch("alert_manager.cli.sys.stdin", InteractiveInput("n\n")), \
                patch("alert_manager.cli.sys.stdout", output), \
                patch("alert_manager.cli.sys.stderr", errors):
            exit_code = cli_main(["--store", str(self.store), "delete", retained["id"]])
        self.assertEqual(exit_code, 0, errors.getvalue())
        self.assertEqual(self.store.read_bytes(), before)
        response_start = output.getvalue().rfind("{")
        self.assertFalse(json.loads(output.getvalue()[response_start:])["deleted"])
        restarted = self.invoke("get", retained["id"])
        self.assertEqual(restarted.returncode, 0, restarted.stderr)

        noninteractive = self.invoke("delete", retained["id"])
        self.assertEqual(noninteractive.returncode, 2)

    def test_summary_has_all_categories_in_canonical_order(self) -> None:
        self.create_alert("One", "High")
        result = self.invoke("summary")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(list(summary["by_severity"]),
                         ["Critical", "High", "Medium", "Low", "Informational"])
        self.assertEqual(list(summary["by_status"]), ["New", "In Progress", "Resolved", "Closed"])

    def test_failed_write_has_error_code_and_preserves_persisted_bytes(self) -> None:
        self.create_alert("Existing")
        original = self.store.read_bytes()
        output = io.StringIO()
        errors = io.StringIO()
        with patch("alert_manager.storage.os.replace", side_effect=OSError("simulated failure")), \
                redirect_stdout(output), redirect_stderr(errors):
            result = cli_main(["--store", str(self.store), "create", "--title", "New",
                               "--description", "New details", "--source-ip", "203.0.113.8",
                               "--severity", "Low"])
        self.assertEqual(result, 5)
        self.assertIn("error:", errors.getvalue())
        self.assertNotIn("Alert created", output.getvalue())
        self.assertEqual(self.store.read_bytes(), original)
        self.assertEqual(JsonAlertStore(self.store).load()[0].title, "Existing")

    def test_duplicate_key_store_fails_cli_closed_without_rewrite(self) -> None:
        fixture = Path(__file__).parents[1] / "fixtures" / "duplicate-json-keys.json"
        original = fixture.read_bytes()
        self.store.write_bytes(original)
        result = self.invoke("list")
        self.assertEqual(result.returncode, 5)
        self.assertIn("error:", result.stderr)
        self.assertEqual(self.store.read_bytes(), original)

    def test_duplicate_id_store_fails_cli_closed_without_rewrite(self) -> None:
        self.create_alert("Duplicate ID seed")
        document = json.loads(self.store.read_text(encoding="utf-8"))
        document["alerts"].append(dict(document["alerts"][0], title="Duplicate ID"))
        original = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
        self.store.write_bytes(original)
        result = self.invoke("list")
        self.assertEqual(result.returncode, 5)
        self.assertIn("error:", result.stderr)
        self.assertEqual(self.store.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
