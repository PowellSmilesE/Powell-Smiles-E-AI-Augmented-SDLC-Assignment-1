"""Strict JSON file persistence with fail-closed loading and atomic replacement."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import Alert
from .service import PersistenceError

MAX_STORE_BYTES = 256 * 1024 * 1024


class _DuplicateJSONKey(ValueError):
    """Raised by the JSON decoder when any object repeats a member name."""


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey("duplicate object key")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


class JsonAlertStore:
    """Load and safely replace one JSON store file.

    The configured path is not opened by construction. Reads fail closed on invalid data, and
    writes use a same-directory temporary file followed by replacement.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        """Create a store for ``path`` without opening or changing the file.

        Args:
            path: Filesystem path used for load and save operations.

        Returns:
            A JSON store instance.
        """
        self.path = Path(path)

    def load(self) -> list[Alert]:
        """Read and validate the entire store; missing means empty, invalid fails closed.

        Returns:
            Validated alerts in persisted order.

        Raises:
            PersistenceError: The file is unreadable, oversized, malformed, or structurally invalid.
        """
        try:
            size = self.path.stat().st_size
            if size > MAX_STORE_BYTES:
                raise PersistenceError("alert store exceeds the 256 MiB size limit")
            with self.path.open("rb") as stream:
                raw = stream.read(MAX_STORE_BYTES + 1)
        except FileNotFoundError:
            return []
        except PersistenceError:
            raise
        except OSError as exc:
            raise PersistenceError("alert store could not be read") from exc

        if len(raw) > MAX_STORE_BYTES:
            raise PersistenceError("alert store exceeds the 256 MiB size limit")
        try:
            document = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_object_without_duplicate_keys,
                parse_constant=_reject_non_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise PersistenceError("alert store contains invalid JSON") from exc

        if not isinstance(document, dict) or set(document) != {"alerts"}:
            raise PersistenceError('alert store must be an object containing only an "alerts" array')
        records = document["alerts"]
        if not isinstance(records, list):
            raise PersistenceError('alert store "alerts" value must be an array')

        alerts: list[Alert] = []
        seen_ids: set[str] = set()
        try:
            for record in records:
                alert = Alert.from_dict(record)
                if alert.id in seen_ids:
                    raise ValueError("duplicate alert ID")
                seen_ids.add(alert.id)
                alerts.append(alert)
        except (TypeError, ValueError) as exc:
            raise PersistenceError("alert store contains an invalid alert record") from exc
        return alerts

    def save(self, alerts: Iterable[Alert]) -> None:
        """Write a validated store using a same-directory temp file and replacement.

        Args:
            alerts: Complete replacement collection to persist.

        Returns:
            ``None`` after successful replacement.

        Raises:
            PersistenceError: Serialization, temporary-file, flush, or replacement fails. The
                original target remains unchanged when replacement does not complete.
        """
        try:
            records = list(alerts)
            if any(not isinstance(alert, Alert) for alert in records):
                raise ValueError("store accepts only validated Alert records")
            identifiers = [alert.id for alert in records]
            if len(identifiers) != len(set(identifiers)):
                raise ValueError("store contains duplicate alert IDs")
            encoded = (json.dumps({"alerts": [alert.to_dict() for alert in records]},
                                  ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise PersistenceError("alert store data could not be serialized") from exc

        temporary_path: str | None = None
        try:
            descriptor, temporary_path = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=str(self.path.parent)
            )
            with os.fdopen(descriptor, "wb") as stream:
                if os.name == "posix":
                    os.fchmod(stream.fileno(), stat.S_IRUSR | stat.S_IWUSR)
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
        except OSError as exc:
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
            raise PersistenceError("alert store could not be safely written") from exc
