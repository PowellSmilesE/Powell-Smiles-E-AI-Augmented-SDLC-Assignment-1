"""Business-layer error types and alert use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from .models import Alert, Severity, Status


class AlertStore(Protocol):
    """Persistence interface used by the business layer."""

    def load(self) -> list[Alert]:
        """Load all validated alert records.

        Returns:
            Persisted alerts.

        Raises:
            PersistenceError: The configured store cannot be read or validated.
        """

    def save(self, alerts: list[Alert]) -> None:
        """Persist a complete replacement alert collection.

        Args:
            alerts: Complete validated alert set to persist.

        Returns:
            ``None`` on success.

        Raises:
            PersistenceError: The replacement could not be persisted safely.
        """


class AlertManagerError(Exception):
    """Base class for expected application failures shown by the CLI."""


class ValidationError(AlertManagerError):
    """Input or requested alert data violates a documented rule."""


class AlertNotFoundError(AlertManagerError):
    """The requested alert identifier is not in the store."""


class PersistenceError(AlertManagerError):
    """The alert store could not be read or safely written."""


class AlertService:
    """Coordinate alert operations while keeping file I/O behind ``AlertStore``."""

    def __init__(
        self,
        store: AlertStore,
        id_provider: Callable[[], UUID] = uuid4,
        clock_provider: Callable[[], datetime] | None = None,
    ) -> None:
        """Set the persistence interface and injectable providers.

        Args:
            store: Interface used to load and replace validated alert collections.
            id_provider: Zero-argument UUID4 provider; defaults to ``uuid4``.
            clock_provider: Zero-argument timezone-aware clock; defaults to current UTC time.

        Returns:
            ``None``.
        """
        self._store = store
        self._id_provider = id_provider
        self._clock_provider = clock_provider or (lambda: datetime.now(UTC))

    def _load(self) -> list[Alert]:
        try:
            return self._store.load()
        except PersistenceError:
            raise
        except OSError as exc:
            raise PersistenceError("alert store could not be read") from exc

    def _save(self, alerts: list[Alert]) -> None:
        try:
            self._store.save(alerts)
        except PersistenceError:
            raise
        except OSError as exc:
            raise PersistenceError("alert store could not be safely written") from exc

    @staticmethod
    def _identifier(value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError("alert ID must be a canonical UUID4")
        try:
            parsed = UUID(value)
        except (ValueError, AttributeError) as exc:
            raise ValidationError("alert ID must be a canonical UUID4") from exc
        if str(parsed) != value or parsed.version != 4:
            raise ValidationError("alert ID must be a canonical UUID4")
        return value

    @staticmethod
    def _severity(value: str | Severity) -> Severity:
        try:
            return Severity(value)
        except (ValueError, TypeError) as exc:
            supported = ", ".join(item.value for item in Severity)
            raise ValidationError(f"severity must be one of: {supported}") from exc

    @staticmethod
    def _status(value: str | Status) -> Status:
        try:
            return Status(value)
        except (ValueError, TypeError) as exc:
            supported = ", ".join(item.value for item in Status)
            raise ValidationError(f"status must be one of: {supported}") from exc

    @staticmethod
    def _sort(alerts: list[Alert]) -> list[Alert]:
        return sorted(alerts, key=lambda alert: UUID(alert.id).int)

    def create(self, title: str, description: str, source_ip: str, severity: str) -> Alert:
        """Create and persist an alert with a unique UUID4 and UTC creation timestamp.

        Args:
            title: Required title of at most 200 characters.
            description: Required description of at most 4,000 characters.
            source_ip: Valid IPv4 or IPv6 address.
            severity: One of the five documented severity labels.

        Returns:
            The newly persisted alert, with status ``New``.

        Raises:
            ValidationError: A supplied field or injected provider value is invalid.
            PersistenceError: The store cannot be read or the new collection cannot be saved.
        """
        alerts = self._load()
        identifiers = {alert.id for alert in alerts}
        selected_id = ""
        while not selected_id:
            candidate = self._id_provider()
            candidate_text = str(candidate)
            try:
                self._identifier(candidate_text)
            except ValidationError as exc:
                raise ValidationError("UUID provider must return a UUID4 value") from exc
            if candidate_text not in identifiers:
                selected_id = candidate_text
        try:
            now = self._clock_provider()
            if now.tzinfo is None or now.utcoffset() is None:
                raise ValueError("clock provider must return a timezone-aware datetime")
            timestamp = now.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            alert = Alert(
                id=selected_id,
                title=title,
                description=description,
                source_ip=source_ip,
                severity=self._severity(severity),
                status=Status.NEW,
                created_at=timestamp,
            )
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError(str(exc)) from exc
        self._save([*alerts, alert])
        return alert

    def list_alerts(self) -> list[Alert]:
        """Return all alerts in ascending UUID order.

        Returns:
            Stored alerts sorted by their UUID values.

        Raises:
            PersistenceError: The store cannot be read or validated.
        """
        return self._sort(self._load())

    def get(self, alert_id: str) -> Alert:
        """Return one alert or raise not found for a valid but absent UUID4.

        Args:
            alert_id: Canonical UUID4 string to retrieve.

        Returns:
            The matching alert.

        Raises:
            ValidationError: ``alert_id`` is not a canonical UUID4.
            AlertNotFoundError: No alert has this UUID4.
            PersistenceError: The store cannot be read or validated.
        """
        identifier = self._identifier(alert_id)
        for alert in self._load():
            if alert.id == identifier:
                return alert
        raise AlertNotFoundError(f"alert {identifier} was not found")

    def search(
        self,
        text: str | None = None,
        severity: str | Severity | None = None,
        status: str | Status | None = None,
    ) -> list[Alert]:
        """Search text and optional severity/status criteria using AND semantics.

        Args:
            text: Optional non-blank case-insensitive substring.
            severity: Optional canonical severity filter.
            status: Optional canonical status filter.

        Returns:
            Matching alerts in ascending UUID order.

        Raises:
            ValidationError: Text is blank or a supplied filter is unsupported.
            PersistenceError: The store cannot be read or validated.
        """
        if text is not None and (not isinstance(text, str) or not text.strip()):
            raise ValidationError("search text must not be blank")
        selected_severity = self._severity(severity) if severity is not None else None
        selected_status = self._status(status) if status is not None else None
        needle = text.casefold() if text is not None else None
        matched = []
        for alert in self._load():
            text_match = needle is None or any(
                needle in value.casefold()
                for value in (alert.title, alert.description, alert.source_ip)
            )
            if (
                text_match
                and (selected_severity is None or alert.severity == selected_severity)
                and (selected_status is None or alert.status == selected_status)
            ):
                matched.append(alert)
        return self._sort(matched)

    def filter(
        self,
        severity: str | Severity | None = None,
        status: str | Status | None = None,
    ) -> list[Alert]:
        """Return alerts matching every supplied classification filter.

        Args:
            severity: Optional canonical severity filter.
            status: Optional canonical status filter.

        Returns:
            Matching alerts in ascending UUID order.

        Raises:
            ValidationError: A supplied filter is unsupported.
            PersistenceError: The store cannot be read or validated.
        """
        return self.search(severity=severity, status=status)

    def update(self, alert_id: str, updates: Mapping[str, str]) -> Alert:
        """Update permitted fields while preserving identity and creation time.

        Args:
            alert_id: Canonical UUID4 of the alert to update.
            updates: Non-empty mapping using only title, description, source_ip, and severity.

        Returns:
            The updated, persisted alert.

        Raises:
            ValidationError: The ID or update fields/values are invalid.
            AlertNotFoundError: The ID is valid but absent from the store.
            PersistenceError: The store cannot be read or the update cannot be saved.
        """
        identifier = self._identifier(alert_id)
        allowed = {"title", "description", "source_ip", "severity"}
        if not isinstance(updates, Mapping) or not updates:
            raise ValidationError("provide at least one permitted field to update")
        unknown = set(updates) - allowed
        if unknown:
            raise ValidationError(f"update contains unsupported field(s): {', '.join(sorted(unknown))}")
        alerts = self._load()
        for index, current in enumerate(alerts):
            if current.id == identifier:
                data = current.to_dict()
                data.update(updates)
                try:
                    updated = Alert.from_dict(data)
                except (TypeError, ValueError) as exc:
                    raise ValidationError(str(exc)) from exc
                changed = list(alerts)
                changed[index] = updated
                self._save(changed)
                return updated
        raise AlertNotFoundError(f"alert {identifier} was not found")

    def change_status(self, alert_id: str, status: str) -> Alert:
        """Set a supported status directly, preserving the alert's identity and time.

        Args:
            alert_id: Canonical UUID4 of the alert to change.
            status: One of the four documented statuses.

        Returns:
            The updated, persisted alert.

        Raises:
            ValidationError: The ID or status is invalid.
            AlertNotFoundError: The ID is valid but absent from the store.
            PersistenceError: The store cannot be read or the update cannot be saved.
        """
        identifier = self._identifier(alert_id)
        selected_status = self._status(status)
        alerts = self._load()
        for index, current in enumerate(alerts):
            if current.id == identifier:
                updated = replace(current, status=selected_status)
                changed = list(alerts)
                changed[index] = updated
                self._save(changed)
                return updated
        raise AlertNotFoundError(f"alert {identifier} was not found")

    def delete(self, alert_id: str) -> Alert:
        """Delete and persist one existing alert; confirmation is handled by the CLI.

        Args:
            alert_id: Canonical UUID4 of the alert to delete.

        Returns:
            The deleted alert.

        Raises:
            ValidationError: ``alert_id`` is not a canonical UUID4.
            AlertNotFoundError: The ID is valid but absent from the store.
            PersistenceError: The store cannot be read or the deletion cannot be saved.
        """
        identifier = self._identifier(alert_id)
        alerts = self._load()
        for index, current in enumerate(alerts):
            if current.id == identifier:
                self._save(alerts[:index] + alerts[index + 1 :])
                return current
        raise AlertNotFoundError(f"alert {identifier} was not found")

    def summary(self) -> dict[str, dict[str, int]]:
        """Return stable counts for every severity and status, including zeroes.

        Returns:
            Ordered ``by_severity`` and ``by_status`` count mappings.

        Raises:
            PersistenceError: The store cannot be read or validated.
        """
        alerts = self._load()
        return {
            "by_severity": {
                severity.value: sum(alert.severity == severity for alert in alerts)
                for severity in Severity
            },
            "by_status": {
                status.value: sum(alert.status == status for alert in alerts)
                for status in Status
            },
        }
