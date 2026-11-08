# CLI Contract: Security Alert Management

This document defines the user-visible command contract. The planned entry point is
`python -m alert_manager`; the default store is `alerts.json` in the current working directory and may be overridden with `--store PATH`; exact other option spellings may be finalized during implementation while
preserving these required behaviors.

## Commands

| Operation | Required behavior |
|---|---|
| `create` | Accept title, description, source IP, and severity; generate UUID4, UTC timestamp, and `New` status; display the created record and ID. |
| `list` | Display all records once in ascending UUID order; empty store prints an empty result. |
| `get <id>` | Display one record; unknown ID reports not found. |
| `search <text> [--severity <value>] [--status <value>]` | Case-insensitive substring match over title, description, and source IP. Severity and status are optional; every supplied search/filter criterion is combined with AND. Results use ascending UUID order. |
| `filter [--severity <value>] [--status <value>]` | Accept severity and/or status without a text query. When searching and filtering together, use the optional flags on `search`; every supplied criterion must match (AND). Results use ascending UUID order. |
| `update <id>` | Update only title, description, source IP, and severity. ID and timestamp are immutable; status uses its own operation. |
| `status <id> <status>` | Set any supported status directly, including backward changes. |
| `delete <id>` | Require an affirmative confirmation for each deletion; declining leaves the record unchanged. A missing ID reports not found. |
| `summary` | Show counts for all severity and status categories, including zero-count categories, in canonical order. |

## Input and output rules

- Severity values: `Critical`, `High`, `Medium`, `Low`, `Informational`.
- Status values: `New`, `In Progress`, `Resolved`, `Closed`.
- Source IP must be IPv4 or IPv6; timestamps are generated, not user-editable.
- Human-readable output goes to stdout. Validation, not-found, and persistence errors go to stderr.
- Exit status `0` means success, including a declined deletion; `2` means command usage error; `3` means invalid input; `4` means alert not found; and `5` means persistence failure. These values are stable contract behavior.
- A missing store is an empty store. Malformed, unreadable, structurally invalid, duplicate-ID, or
  duplicate-object-key JSON data returns persistence error code `5` and is preserved byte-for-byte
  without reset or rewrite.
- Delete requires an interactive confirmation or an explicit affirmative flag when run
  non-interactively. No implicit bulk deletion is supported.
- Every list/search/filter result uses ascending UUID order. No alternate sorting modes are exposed.

## Persistence behavior

Successful mutations persist before reporting success. If persistence fails, the command reports an
error and must not claim the mutation succeeded. Updating or deleting an unknown ID reports not
found and does not change other records. A failed store load blocks commands that need store data.

The store is local, single-user, and plaintext. Encryption at rest is outside scope. On POSIX,
created/replaced store files and temporary siblings must have mode `0600`; on Windows, they inherit
a parent directory ACL restricted to the current user. Acceptance checks POSIX permission bits or
the effective Windows ACL, as applicable.
