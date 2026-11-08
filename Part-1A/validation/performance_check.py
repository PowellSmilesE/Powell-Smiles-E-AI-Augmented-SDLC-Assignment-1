"""Measure the 10,000-alert CLI acceptance operations without importing app code."""

from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from time import perf_counter
from uuid import uuid4


COUNT = 10_000
SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="alert-manager-performance-") as temporary:
        store = Path(temporary) / "alerts.json"
        records = []
        for index in range(COUNT):
            records.append({
                "id": str(uuid4()),
                "title": f"Alert {index:05d}",
                "description": "Performance acceptance fixture",
                "source_ip": "203.0.113.9",
                "severity": ("Critical", "High", "Medium", "Low", "Informational")[index % 5],
                "status": ("New", "In Progress", "Resolved", "Closed")[index % 4],
                "created_at": "2026-11-04T12:30:45Z",
            })
        store.write_text(json.dumps({"alerts": records}, separators=(",", ":")), encoding="utf-8")
        selected = records[0]["id"]
        environment = os.environ.copy()
        old_pythonpath = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(SOURCE_ROOT) if not old_pythonpath else (
            str(SOURCE_ROOT) + os.pathsep + old_pythonpath
        )

        operations = {
            "list": ("list",),
            "id_lookup": ("get", selected),
            "filter": ("filter", "--severity", "High", "--status", "New"),
            "summary": ("summary",),
        }
        timings: dict[str, float] = {}
        for name, arguments in operations.items():
            started = perf_counter()
            result = subprocess.run(
                [sys.executable, "-m", "alert_manager", "--store", str(store), *arguments],
                capture_output=True,
                text=True,
                env=environment,
                timeout=30,
                check=False,
            )
            elapsed = perf_counter() - started
            timings[name] = elapsed
            if result.returncode != 0:
                print(f"FAIL {name}: exit {result.returncode}: {result.stderr.strip()}")
                return 1
            decoded = json.loads(result.stdout)
            if name == "list" and len(decoded) != COUNT:
                print(f"FAIL list: expected {COUNT} records, got {len(decoded)}")
                return 1
            if name == "id_lookup" and decoded["id"] != selected:
                print("FAIL id_lookup: returned a different ID")
                return 1
            if name == "filter" and not decoded:
                print("FAIL filter: expected matching records")
                return 1
            if name == "summary" and sum(decoded["by_severity"].values()) != COUNT:
                print("FAIL summary: severity count total did not match store")
                return 1

        print(f"Environment: {platform.platform()}; Python {platform.python_version()}")
        print(f"Dataset: {COUNT} alerts")
        for name, seconds in timings.items():
            print(f"{name}: {seconds:.4f} seconds")
        failures = [name for name, seconds in timings.items() if seconds >= 2.0]
        if failures:
            print("FAIL threshold: " + ", ".join(failures) + " exceeded 2 seconds")
            return 1
        print("PASS all operations completed in under 2 seconds")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
