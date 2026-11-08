"""Unit tests for deterministic alert business rules."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from uuid import UUID

from alert_manager.models import Alert, Severity, Status
from alert_manager.service import AlertNotFoundError, AlertService, ValidationError

BASE_RECORD = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Suspicious login",
    "description": "Repeated failed login attempts.",
    "source_ip": "203.0.113.7",
    "severity": "High",
    "status": "New",
    "created_at": "2026-11-04T12:30:45Z",
}


class MemoryStore:
    def __init__(self, alerts: list[Alert] | None = None) -> None:
        self.alerts = list(alerts or [])

    def load(self) -> list[Alert]:
        return list(self.alerts)

    def save(self, alerts: list[Alert]) -> None:
        self.alerts = list(alerts)


class AlertServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generated_ids = iter(
            UUID(value)
            for value in (
                "550e8400-e29b-41d4-a716-446655440000",
                "550e8400-e29b-41d4-a716-446655440001",
                "550e8400-e29b-41d4-a716-446655440002",
            )
        )
        self.clock = lambda: datetime(2026, 11, 4, 12, 30, 45, tzinfo=UTC)
        self.store = MemoryStore()
        self.service = AlertService(self.store, id_provider=lambda: next(self.generated_ids), clock_provider=self.clock)

    def test_create_assigns_uuid4_timestamp_and_default_status(self) -> None:
        alert = self.service.create("Suspicious login", "Repeated failures", "203.0.113.7", "High")
        self.assertEqual(alert.id, "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(alert.status, Status.NEW)
        self.assertEqual(alert.created_at, "2026-11-04T12:30:45Z")
        self.assertEqual(self.store.load(), [alert])

    def test_create_retries_uuid4_collision(self) -> None:
        existing = Alert.from_dict(BASE_RECORD)
        generated = iter((UUID(existing.id), UUID("550e8400-e29b-41d4-a716-446655440001")))
        service = AlertService(MemoryStore([existing]), id_provider=lambda: next(generated), clock_provider=self.clock)
        created = service.create("Second", "Another alert", "2001:db8::1", "Low")
        self.assertEqual(created.id, "550e8400-e29b-41d4-a716-446655440001")

    def test_list_is_stably_sorted_by_uuid(self) -> None:
        second = Alert.from_dict(dict(BASE_RECORD, id="550e8400-e29b-41d4-a716-446655440002"))
        first = Alert.from_dict(BASE_RECORD)
        service = AlertService(MemoryStore([second, first]))
        self.assertEqual([alert.id for alert in service.list_alerts()], [first.id, second.id])

    def test_get_returns_record_and_unknown_id_raises(self) -> None:
        existing = Alert.from_dict(BASE_RECORD)
        service = AlertService(MemoryStore([existing]))
        self.assertEqual(service.get(existing.id), existing)
        with self.assertRaises(AlertNotFoundError):
            service.get("550e8400-e29b-41d4-a716-446655440001")

    def test_create_rejects_invalid_fields_before_saving(self) -> None:
        for severity in ("Urgent", ""):
            with self.subTest(severity=severity), self.assertRaises(ValidationError):
                self.service.create("Good", "Good description", "203.0.113.7", severity)
        self.assertEqual(self.store.load(), [])

    def _seed(self) -> list[Alert]:
        alerts = [
            Alert.from_dict(dict(BASE_RECORD, id="550e8400-e29b-41d4-a716-446655440000")),
            Alert.from_dict(dict(BASE_RECORD, id="550e8400-e29b-41d4-a716-446655440001",
                                 title="Malware beacon", severity="Critical", status="In Progress")),
            Alert.from_dict(dict(BASE_RECORD, id="550e8400-e29b-41d4-a716-446655440002",
                                 title="Suspicious login from test network", severity="High",
                                 status="Resolved")),
        ]
        self.store = MemoryStore(alerts)
        self.service = AlertService(self.store, id_provider=lambda: next(self.generated_ids), clock_provider=self.clock)
        return alerts

    def test_search_uses_case_insensitive_text_and_and_filters(self) -> None:
        self._seed()
        matches = self.service.search("SUSPICIOUS", severity="High", status="New")
        self.assertEqual([alert.id for alert in matches], ["550e8400-e29b-41d4-a716-446655440000"])
        self.assertEqual(len(self.service.search("suspicious", status="Resolved")), 1)
        self.assertEqual(len(self.service.search("suspicious", severity="Critical")), 0)
        self.assertEqual(len(self.service.filter(severity="Critical", status="In Progress")), 1)
        self.assertEqual(self.service.search("no such text"), [])

    def test_search_sorts_by_uuid_and_matches_source_ip(self) -> None:
        seeded = self._seed()
        matches = self.service.search("203.0.113.7")
        self.assertEqual([alert.id for alert in matches], sorted(alert.id for alert in seeded))

    def test_update_changes_only_permitted_fields_and_preserves_identity_time(self) -> None:
        self._seed()
        original = self.service.get("550e8400-e29b-41d4-a716-446655440000")
        updated = self.service.update(original.id, {
            "title": "Updated title", "description": "Updated details",
            "source_ip": "2001:db8::1", "severity": "Low",
        })
        self.assertEqual(updated.title, "Updated title")
        self.assertEqual(updated.description, "Updated details")
        self.assertEqual(updated.source_ip, "2001:db8::1")
        self.assertEqual(updated.severity, Severity.LOW)
        self.assertEqual(updated.id, original.id)
        self.assertEqual(updated.created_at, original.created_at)
        self.assertEqual(updated.status, original.status)

    def test_status_can_transition_directly_between_every_supported_value(self) -> None:
        self._seed()
        alert_id = "550e8400-e29b-41d4-a716-446655440000"
        for status in Status:
            changed = self.service.change_status(alert_id, status.value)
            self.assertEqual(changed.status, status)
            self.assertEqual(changed.id, alert_id)
            self.assertEqual(changed.created_at, BASE_RECORD["created_at"])

    def test_rejected_mutations_report_validation_error_and_do_not_change_store(self) -> None:
        self._seed()
        alert_id = "550e8400-e29b-41d4-a716-446655440000"
        original = self.store.load()
        invalid_updates = (
            {"title": "  "}, {"title": "x" * 201}, {"description": ""},
            {"description": "x" * 4001}, {"source_ip": "host.invalid"},
            {"severity": "Urgent"}, {"status": "Closed"}, {"unknown": "value"},
        )
        for updates in invalid_updates:
            with self.subTest(updates=updates):
                with self.assertRaises(ValidationError):
                    self.service.update(alert_id, updates)
                self.assertEqual(self.store.load(), original)

        for operation in (
            lambda: self.service.change_status(alert_id, "Waiting"),
            lambda: self.service.update("550e8400-e29b-41d4-a716-446655440099", {"title": "ok"}),
            lambda: self.service.change_status("550e8400-e29b-41d4-a716-446655440099", "Closed"),
            lambda: self.service.delete("550e8400-e29b-41d4-a716-446655440099"),
        ):
            with self.assertRaises((ValidationError, AlertNotFoundError)):
                operation()
            self.assertEqual(self.store.load(), original)

    def test_delete_and_summary_cover_records_and_zero_categories(self) -> None:
        self._seed()
        deleted = self.service.delete("550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(deleted.id, "550e8400-e29b-41d4-a716-446655440000")
        summary = self.service.summary()
        self.assertEqual(summary["by_severity"]["Critical"], 1)
        self.assertEqual(summary["by_status"]["In Progress"], 1)
        self.assertEqual(summary["by_severity"]["Informational"], 0)
        self.assertEqual(summary["by_status"]["Closed"], 0)

    def test_empty_summary_has_zero_for_every_category(self) -> None:
        summary = self.service.summary()
        self.assertEqual(list(summary["by_severity"].values()), [0] * 5)
        self.assertEqual(list(summary["by_status"].values()), [0] * 4)


if __name__ == "__main__":
    unittest.main()
