"""Command-line interface for Security Alert Management."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import TextIO

from .service import (
    AlertManagerError,
    AlertNotFoundError,
    AlertService,
    PersistenceError,
    ValidationError,
)
from .storage import JsonAlertStore


class _UsageError(Exception):
    """Raised when a command is missing required invocation syntax."""


class _ArgumentParser(argparse.ArgumentParser):
    """Argument parser that keeps usage failures on the documented exit code."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="alert-manager",
        description="Record, search, track, and report security alerts.",
    )
    parser.add_argument("--store", default="alerts.json", help="JSON store path (default: alerts.json)")
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create an alert")
    create.add_argument("--title", required=True)
    create.add_argument("--description", required=True)
    create.add_argument("--source-ip", required=True)
    create.add_argument("--severity", required=True)

    commands.add_parser("list", help="list all alerts")

    get = commands.add_parser("get", help="retrieve an alert by ID")
    get.add_argument("id")

    search = commands.add_parser("search", help="search alert text with optional filters")
    search.add_argument("text")
    search.add_argument("--severity")
    search.add_argument("--status")

    filtered = commands.add_parser("filter", help="filter by severity and/or status")
    filtered.add_argument("--severity")
    filtered.add_argument("--status")

    update = commands.add_parser("update", help="update permitted alert fields")
    update.add_argument("id")
    update.add_argument("--title")
    update.add_argument("--description")
    update.add_argument("--source-ip")
    update.add_argument("--severity")

    status = commands.add_parser("status", help="change investigation status")
    status.add_argument("id")
    status.add_argument("status")

    delete = commands.add_parser("delete", help="delete an alert after confirmation")
    delete.add_argument("id")
    delete.add_argument("--yes", action="store_true", help="confirm deletion non-interactively")

    commands.add_parser("summary", help="show alert counts by severity and status")
    return parser


def _write_json(value: object, stream: TextIO) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)


def _confirm_delete(alert_id: str, confirmed: bool, input_stream: TextIO, output_stream: TextIO) -> bool:
    if confirmed:
        return True
    if not input_stream.isatty():
        raise _UsageError("delete requires --yes when input is not interactive")
    output_stream.write(f"Delete alert {alert_id}? [y/N] ")
    output_stream.flush()
    answer = input_stream.readline().strip().casefold()
    return answer in {"y", "yes"}


def _execute(arguments: argparse.Namespace, input_stream: TextIO, output_stream: TextIO) -> int:
    service = AlertService(JsonAlertStore(arguments.store))
    command = arguments.command

    if command == "create":
        alert = service.create(arguments.title, arguments.description, arguments.source_ip, arguments.severity)
        _write_json({"message": "Alert created", "alert": alert.to_dict()}, output_stream)
    elif command == "list":
        _write_json([alert.to_dict() for alert in service.list_alerts()], output_stream)
    elif command == "get":
        _write_json(service.get(arguments.id).to_dict(), output_stream)
    elif command == "search":
        result = service.search(arguments.text, arguments.severity, arguments.status)
        _write_json([alert.to_dict() for alert in result], output_stream)
    elif command == "filter":
        result = service.filter(arguments.severity, arguments.status)
        _write_json([alert.to_dict() for alert in result], output_stream)
    elif command == "update":
        updates = {
            "title": arguments.title,
            "description": arguments.description,
            "source_ip": arguments.source_ip,
            "severity": arguments.severity,
        }
        selected = {key: value for key, value in updates.items() if value is not None}
        _write_json(service.update(arguments.id, selected).to_dict(), output_stream)
    elif command == "status":
        _write_json(service.change_status(arguments.id, arguments.status).to_dict(), output_stream)
    elif command == "delete":
        current = service.get(arguments.id)
        if not _confirm_delete(current.id, arguments.yes, input_stream, output_stream):
            _write_json({"deleted": False, "id": current.id}, output_stream)
            return 0
        deleted = service.delete(current.id)
        _write_json({"deleted": True, "id": deleted.id}, output_stream)
    elif command == "summary":
        _write_json(service.summary(), output_stream)
    else:
        raise AssertionError("unhandled command")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, execute one operation, and return its stable exit code.

    Args:
        argv: Optional argument vector; defaults to the process command line.

    Returns:
        Exit code 0, 2, 3, 4, or 5 according to the CLI contract.

    Raises:
        No expected application exceptions escape; they are rendered on stderr and mapped to the
        documented exit codes. Unexpected programming errors are not silently hidden.
    """
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    try:
        return _execute(arguments, sys.stdin, sys.stdout)
    except _UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except AlertNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
    except PersistenceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 5
    except AlertManagerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 5
