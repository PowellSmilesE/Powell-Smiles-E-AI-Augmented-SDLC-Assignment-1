"""Independent black-box acceptance checks through the documented CLI only."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from uuid import UUID


SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "duplicate-json-keys.json"


def invoke(store: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    current_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(SOURCE_ROOT) if not current_path else str(SOURCE_ROOT) + os.pathsep + current_path
    )
    return subprocess.run(
        [sys.executable, "-m", "alert_manager", "--store", str(store), *arguments],
        capture_output=True,
        text=True,
        env=environment,
        timeout=20,
        check=False,
    )


def main() -> int:
    passed = 0
    failures: list[str] = []

    def check(name: str, action: object) -> None:
        nonlocal passed
        try:
            assert callable(action)
            action()
            print(f"PASS {name}")
            passed += 1
        except Exception as exc:  # report each scenario and continue for complete evidence
            message = f"FAIL {name}: {type(exc).__name__}: {exc}"
            print(message)
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix="alert-manager-harness-") as temporary:
        root = Path(temporary)
        store = root / "alerts.json"

        def empty_store() -> None:
            result = invoke(store, "list")
            assert result.returncode == 0, result.stderr
            assert json.loads(result.stdout) == []

        check("missing store loads as empty", empty_store)

        def creation_and_retrieval() -> dict[str, str]:
            result = invoke(store, "create", "--title", "Harness suspicious login",
                            "--description", "Independent harness event", "--source-ip", "203.0.113.8",
                            "--severity", "High")
            assert result.returncode == 0, result.stderr
            alert = json.loads(result.stdout)["alert"]
            parsed = UUID(alert["id"])
            assert parsed.version == 4
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", alert["created_at"])
            listed = invoke(store, "list")
            assert listed.returncode == 0, listed.stderr
            assert json.loads(listed.stdout) == [alert]
            got = invoke(store, "get", alert["id"])
            assert got.returncode == 0, got.stderr
            assert json.loads(got.stdout) == alert
            return alert

        created: dict[str, str] = {}

        def create_alert() -> None:
            created.update(creation_and_retrieval())

        check("create, list, get, UUID4, and UTC timestamp", create_alert)

        def combined_search() -> None:
            result = invoke(store, "search", "HARNESS", "--severity", "High", "--status", "New")
            assert result.returncode == 0, result.stderr
            found = json.loads(result.stdout)
            assert [item["id"] for item in found] == [created["id"]]
            assert invoke(store, "search", "HARNESS", "--severity", "Critical").stdout.strip() == "[]"

        check("case-insensitive combined search with AND filters", combined_search)

        def update_and_status_restart() -> None:
            update_result = invoke(store, "update", created["id"], "--title", "Harness updated",
                                   "--source-ip", "2001:db8::8", "--severity", "Low")
            assert update_result.returncode == 0, update_result.stderr
            status_result = invoke(store, "status", created["id"], "Resolved")
            assert status_result.returncode == 0, status_result.stderr
            restarted = invoke(store, "get", created["id"])
            assert restarted.returncode == 0, restarted.stderr
            record = json.loads(restarted.stdout)
            assert record["title"] == "Harness updated"
            assert record["source_ip"] == "2001:db8::8"
            assert record["severity"] == "Low"
            assert record["status"] == "Resolved"
            assert record["id"] == created["id"]
            assert record["created_at"] == created["created_at"]

        check("update and status persist across separate processes", update_and_status_restart)

        def invalid_mutation_preserves_store() -> None:
            before = store.read_bytes()
            result = invoke(store, "update", created["id"], "--title", " ")
            assert result.returncode == 3, result.stderr
            assert result.stderr.strip()
            assert store.read_bytes() == before

        check("rejected update reports an error and preserves bytes", invalid_mutation_preserves_store)

        def summary_categories() -> None:
            result = invoke(store, "summary")
            assert result.returncode == 0, result.stderr
            summary = json.loads(result.stdout)
            assert list(summary["by_severity"]) == ["Critical", "High", "Medium", "Low", "Informational"]
            assert list(summary["by_status"]) == ["New", "In Progress", "Resolved", "Closed"]
            assert summary["by_status"]["Resolved"] == 1

        check("summary includes every canonical category", summary_categories)

        def duplicate_key_fails_closed() -> None:
            duplicate_store = root / "duplicate.json"
            original = FIXTURE.read_bytes()
            duplicate_store.write_bytes(original)
            result = invoke(duplicate_store, "list")
            assert result.returncode == 5, result.stderr
            assert result.stderr.strip()
            assert duplicate_store.read_bytes() == original

        check("duplicate object key store is rejected without rewrite", duplicate_key_fails_closed)

        def confirmed_delete_persists() -> None:
            result = invoke(store, "delete", created["id"], "--yes")
            assert result.returncode == 0, result.stderr
            restarted = invoke(store, "get", created["id"])
            assert restarted.returncode == 4

        check("confirmed deletion persists across processes", confirmed_delete_persists)

    print(f"RESULT: {passed} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
