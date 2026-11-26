# Audit Log Service

A REST API for recording, querying, verifying, and exporting audit events.

Built with Python, FastAPI, SQLite, and SHA-256 hash chaining.

## Features

- Create persistent audit events
- Validate structured event input
- Link consecutive events using SHA-256 hashes
- Verify stored events and predecessor hash references
- Detect ordinary database tampering
- Filter events by actor, event type, resource, and time range
- Paginate query results
- Export events by actor ID or resource ID
- Run automated tests using pytest

## Technology

- Python 3.12
- FastAPI
- Pydantic
- SQLite
- pytest

## Setup

Clone the repository and enter the project directory.

Create a virtual environment:

    python3 -m venv .venv

Activate it on macOS or Linux:

    source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

Start the API:

    uvicorn app.main:app --reload

Open the interactive API documentation:

    http://127.0.0.1:8000/docs

The SQLite database is initialized when the application starts.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Service health check |
| POST | /audit | Create an audit event |
| GET | /audit | Query and filter events |
| GET | /audit/verify | Verify the complete hash chain |
| GET | /audit/export | Export events by actor or resource |

## Example: Create an Audit Event

POST /audit

Request body:

    {
      "eventType": "ACCOUNT_VIEWED",
      "actorId": "employee_101",
      "resourceType": "ACCOUNT",
      "resourceId": "account_789",
      "payload": {
        "action": "VIEW",
        "result": "SUCCESS"
      }
    }

The timestamp is optional. The server generates a UTC timestamp
when one is not supplied.

The response includes the event ID, timestamp, content hash,
and predecessor hash.

## Query Examples

Filter by actor:

    GET /audit?actorId=employee_101

Filter by resource:

    GET /audit?resourceType=ACCOUNT&resourceId=account_789

Filter by event type:

    GET /audit?eventType=ACCOUNT_VIEWED

Paginate:

    GET /audit?limit=10&offset=0

Filter by time:

    GET /audit?startTime=2026-01-01T00:00:00Z

## Verification

    GET /audit/verify

The service recalculates stored event hashes and checks
predecessor references.

It reports the first detected inconsistency.

## Export

    GET /audit/export?actorId=employee_101

    GET /audit/export?resourceId=account_789

The service verifies the complete stored chain before returning
matching events in JSON format.

The exported subset does not include an independent
cryptographic proof of completeness.

## Testing

Run:

    python -m pytest -v

Tests cover ingestion, validation, persistence, hash linkage,
tampering detection, filtering, pagination, UTC timestamp
handling, and export.

## Engineering Documentation

See:

- docs/engineering-decisions.md
- docs/ai-usage-log.md

## Security Limitations

This is a prototype, not a production-ready compliance system.

- No authentication or authorization
- No independent trusted hash checkpoint
- No database-level immutability
- No guaranteed detection of missing or deleted events
- No independently verifiable filtered exports
- No retention or redaction implementation
- No production monitoring or rate limiting
- Timestamp filtering requires additional boundary hardening

A privileged database attacker could rewrite the entire
chain and recompute its hashes.

## Scope

The project implements the core audit logging workflow
and filtered JSON export.

Retention, redaction, and production compliance controls
are documented as future work rather than complete features.
