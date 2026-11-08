# Data Model: Security Alert Management

## Alert

One persisted security alert.

| Field | Type / format | Required | Rules |
|---|---|---:|---|
| `id` | UUID string, canonical form | Yes | Generated as UUID4; unique in the store; immutable. Retry generation on collision. |
| `title` | String | Yes | Non-empty after trimming; at most 200 Unicode characters. |
| `description` | String | Yes | Non-empty after trimming; at most 4,000 Unicode characters. |
| `source_ip` | String | Yes | Must parse as IPv4 or IPv6; hostnames and CIDR ranges are invalid. |
| `severity` | Enum string | Yes | `Critical`, `High`, `Medium`, `Low`, `Informational`, in that order. |
| `status` | Enum string | Yes | `New`, `In Progress`, `Resolved`, or `Closed`. Any status may transition directly to any other. New records default to `New`. |
| `created_at` | String | Yes | UTC RFC 3339, whole seconds, trailing `Z`, e.g. `2026-11-04T12:30:45Z`; immutable. |

The business service owns creation defaults, ID uniqueness, permitted updates, status assignment,
search/filter logic, stable ordering, and summary calculations. The persistence layer validates
records again when loading JSON so invalid on-disk data never reaches business operations.

## JSON Store

The file is UTF-8 JSON with this logical shape:

```json
{
  "alerts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Suspicious login",
      "description": "Repeated failed login attempts from one source.",
      "source_ip": "203.0.113.7",
      "severity": "High",
      "status": "New",
      "created_at": "2026-11-04T12:30:45Z"
    }
  ]
}
```

The file MUST be no larger than 256 MiB before parsing. A missing file loads as an empty collection. Repeated object member names (duplicate JSON object keys) at any depth are invalid, as are duplicate IDs, malformed JSON, invalid root shape,
missing/extra invalid fields, unsupported enum values, invalid IPs, or invalid timestamps reject the
whole document. Rejection does not rewrite or truncate the original file. An empty collection is
persisted as `{"alerts": []}` after a successful mutation that leaves no records.

The store is local, single-user, and plaintext; encryption at rest is outside scope. On POSIX,
created and replaced store files and their temporary siblings use mode `0600`, verified by checking
permission bits. On Windows, files inherit the parent directory ACL; the directory ACL must grant
access only to the current user, and acceptance verifies the effective ACL.

## Derived Alert Summary

Summary is computed from the current alert collection; it is not persisted.

- `by_severity`: counts for all five severity values, including zero counts.
- `by_status`: counts for all four status values, including zero counts.

Both maps use the canonical order listed above. Search and filter results sort by ascending UUID.
