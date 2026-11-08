"""Validated immutable alert data and canonical classification values."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class Severity(str, Enum):
    """Supported alert severities in canonical reporting order."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class Status(str, Enum):
    """Supported investigation states."""

    NEW = "New"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


_ALERT_KEYS = {
    "id",
    "title",
    "description",
    "source_ip",
    "severity",
    "status",
    "created_at",
}
_UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


def _require_text(field: str, value: Any, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text")
    if not value.strip():
        raise ValueError(f"{field} must not be blank")
    if len(value) > maximum:
        raise ValueError(f"{field} must be at most {maximum} characters")
    return value


def _require_uuid4(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("id must be a canonical UUID4 string")
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError("id must be a canonical UUID4 string") from exc
    if str(parsed) != value or parsed.version != 4:
        raise ValueError("id must be a canonical UUID4 string")
    return value


def _require_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not _UTC_TIMESTAMP.fullmatch(value):
        raise ValueError("created_at must be UTC RFC 3339 with whole seconds and trailing Z")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError("created_at must be a valid UTC calendar timestamp") from exc
    return value


def _require_ip(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("source_ip must be a valid IPv4 or IPv6 address")
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError("source_ip must be a valid IPv4 or IPv6 address") from exc
    return value


def _require_enum(field: str, value: Any, enum_type: type[Enum]) -> Enum:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be one of the supported values")
    try:
        return enum_type(value)
    except ValueError as exc:
        supported = ", ".join(item.value for item in enum_type)
        raise ValueError(f"{field} must be one of: {supported}") from exc


@dataclass(frozen=True, slots=True)
class Alert:
    """A validated alert whose identifier and creation time are immutable.

    Fields are the seven documented on-disk values. Construction validates canonical UUID4,
    required bounded text, IP address, severity, status, and UTC timestamp. Invalid values raise
    ``TypeError`` or ``ValueError``; records cannot be modified after construction.
    """

    id: str
    title: str
    description: str
    source_ip: str
    severity: Severity
    status: Status
    created_at: str

    def __post_init__(self) -> None:
        _require_uuid4(self.id)
        _require_text("title", self.title, 200)
        _require_text("description", self.description, 4000)
        _require_ip(self.source_ip)
        object.__setattr__(self, "severity", _require_enum("severity", self.severity, Severity))
        object.__setattr__(self, "status", _require_enum("status", self.status, Status))
        _require_timestamp(self.created_at)

    @classmethod
    def from_dict(cls, record: Mapping[str, Any]) -> Alert:
        """Create an alert from a complete JSON-compatible record.

        Args:
            record: Mapping containing exactly the seven documented alert fields.

        Returns:
            A validated immutable alert.

        Raises:
            TypeError: A field has the wrong runtime type.
            ValueError: Fields are missing, extra, or violate an alert rule.
        """
        if not isinstance(record, Mapping) or set(record) != _ALERT_KEYS:
            raise ValueError("alert record must contain exactly the documented fields")
        return cls(
            id=record["id"],
            title=record["title"],
            description=record["description"],
            source_ip=record["source_ip"],
            severity=_require_enum("severity", record["severity"], Severity),  # type: ignore[arg-type]
            status=_require_enum("status", record["status"], Status),  # type: ignore[arg-type]
            created_at=record["created_at"],
        )

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-compatible record in stable field order.

        Returns:
            A new mapping with the alert fields and canonical enum values.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source_ip": self.source_ip,
            "severity": self.severity.value,
            "status": self.status.value,
            "created_at": self.created_at,
        }
