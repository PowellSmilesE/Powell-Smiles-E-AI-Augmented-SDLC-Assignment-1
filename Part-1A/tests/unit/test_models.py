"""Unit tests for alert data validation and immutability."""

import unittest
from dataclasses import FrozenInstanceError

from alert_manager.models import Alert, Severity, Status

VALID_ALERT = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Suspicious login",
    "description": "Repeated failed login attempts.",
    "source_ip": "203.0.113.7",
    "severity": "High",
    "status": "New",
    "created_at": "2026-11-04T12:30:45Z",
}


class AlertModelTests(unittest.TestCase):
    def test_valid_record_round_trips_with_canonical_values(self) -> None:
        alert = Alert.from_dict(VALID_ALERT)
        self.assertEqual(alert.to_dict(), VALID_ALERT)
        self.assertEqual([item.value for item in Severity], ["Critical", "High", "Medium", "Low", "Informational"])
        self.assertEqual([item.value for item in Status], ["New", "In Progress", "Resolved", "Closed"])

    def test_alert_is_immutable(self) -> None:
        alert = Alert.from_dict(VALID_ALERT)
        with self.assertRaises(FrozenInstanceError):
            alert.title = "Changed"  # type: ignore[misc]

    def test_rejects_blank_and_over_limit_text(self) -> None:
        for field in ("title", "description"):
            with self.subTest(field=field, value="blank"):
                record = dict(VALID_ALERT, **{field: "  \t "})
                with self.assertRaises(ValueError):
                    Alert.from_dict(record)

        with self.assertRaises(ValueError):
            Alert.from_dict(dict(VALID_ALERT, title="x" * 201))
        with self.assertRaises(ValueError):
            Alert.from_dict(dict(VALID_ALERT, description="x" * 4001))

    def test_accepts_exact_text_limits(self) -> None:
        Alert.from_dict(dict(VALID_ALERT, title="x" * 200, description="y" * 4000))

    def test_rejects_invalid_ip_addresses(self) -> None:
        for value in ("host.example", "203.0.113.0/24", "999.1.1.1", " 203.0.113.7"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Alert.from_dict(dict(VALID_ALERT, source_ip=value))

    def test_accepts_ipv4_and_ipv6(self) -> None:
        Alert.from_dict(dict(VALID_ALERT, source_ip="203.0.113.7"))
        Alert.from_dict(dict(VALID_ALERT, source_ip="2001:db8::7"))

    def test_rejects_unsupported_severity_and_status(self) -> None:
        for field, value in (("severity", "Urgent"), ("status", "Pending")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                Alert.from_dict(dict(VALID_ALERT, **{field: value}))

    def test_rejects_invalid_uuid_and_timestamp(self) -> None:
        for field, value in (
            ("id", "550e8400-e29b-11d4-a716-446655440000"),
            ("id", "not-a-uuid"),
            ("created_at", "2026-11-04T12:30:45+00:00"),
            ("created_at", "2026-02-30T12:30:45Z"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                Alert.from_dict(dict(VALID_ALERT, **{field: value}))

    def test_rejects_missing_extra_and_non_string_fields(self) -> None:
        with self.assertRaises(ValueError):
            Alert.from_dict({key: value for key, value in VALID_ALERT.items() if key != "title"})
        with self.assertRaises(ValueError):
            Alert.from_dict(dict(VALID_ALERT, unexpected="value"))
        with self.assertRaises((TypeError, ValueError)):
            Alert.from_dict(dict(VALID_ALERT, title=7))


if __name__ == "__main__":
    unittest.main()
