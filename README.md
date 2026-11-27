# Audit Log Service

A Python/FastAPI prototype for recording, querying, verifying, and exporting tamper-evident audit events.

The service implements SHA-256 hash chaining, SQLite persistence, logical archival, structured redaction, Ed25519-signed exports, and client-account access auditing.

## Features

- Persistent audit event ingestion with structured validation
- SHA-256 hash chaining and integrity verification
- Detection of ordinary modifications to stored audit events
- Filtering by actor, event type, resource, and time range
- Pagination with validated limits
- Configurable logical archival of older events
- Field-level redaction in API responses without modifying original hashed records
- Filtered JSON exports signed using Ed25519
- Offline export signature verification using a trusted public key
- Dedicated client-account access audit endpoint
- Automated tests using pytest

## Technology

Python 3.12, FastAPI, Pydantic, SQLite, pytest, and cryptography.

## Setup

Clone the repository and enter the project directory.

Create and activate a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

Generate a local signing key before using signed exports:

    python -c "from app.signing_service import generate_signing_key; generate_signing_key()"

The signing key is stored in `.audit_signing_key.pem` and must remain private. The file is excluded from Git.

Start the API:

    uvicorn app.main:app --reload

Interactive API documentation:

    http://127.0.0.1:8000/docs

The SQLite database is initialized when the application starts.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /audit | Create an audit event |
| GET | /audit | Query and filter events |
| GET | /audit/verify | Verify the hash chain |
| GET | /audit/export | Export signed records by actor or resource |
| POST | /audit/archive | Logically archive expired records |
| POST | /audit/{event_id}/redact | Register a payload field for response redaction |
| POST | /audit/account-access | Record a client-account access attempt |

## Example: Create an Audit Event

POST /audit

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

The timestamp is optional; the server generates a UTC timestamp if omitted.

The response includes the event ID, timestamp, content hash, and predecessor hash.

## Query Examples

    GET /audit?actorId=employee_101
    GET /audit?resourceType=ACCOUNT&resourceId=account_789
    GET /audit?eventType=ACCOUNT_VIEWED
    GET /audit?limit=10&offset=0
    GET /audit?startTime=2026-01-01T00:00:00Z

## Integrity Verification

    GET /audit/verify

The service recalculates event hashes and checks predecessor references.

It reports whether the stored chain is valid and identifies the first detected inconsistency.

The hash chain is not independently anchored outside the database.

## Retention and Logical Archival

The default retention window is 365 days.

Configure it before starting the application:

    export AUDIT_RETENTION_DAYS=90

Trigger archival:

    POST /audit/archive

Expired events are marked with an archival timestamp. They are not physically deleted or moved to separate storage.

This preserves the existing hash chain but is not a complete retention or deletion solution.

## Structured Redaction

Example:

    POST /audit/1/redact

Request body:

    {
      "fieldPath": "customer.email"
    }

The query and export APIs replace the selected field with `[REDACTED]`.

The original hashed event remains unchanged in SQLite.

This is presentation-layer redaction, not secure erasure of sensitive data.

## Signed Exports

Examples:

    GET /audit/export?actorId=employee_101
    GET /audit/export?resourceId=account_789

Exports include a signed bundle containing the selected records, filters, metadata, and verification result.

The service uses Ed25519 signatures.

To save an export, request the endpoint and write the JSON response to a file.

Export the corresponding public key:

    python -c "from app.signing_service import public_key_pem; print(public_key_pem())" > audit_public_key.pem

Verify an export offline:

    python -m scripts.verify_export export.json audit_public_key.pem

The public key must be obtained through a trusted channel. A signature proves that the signed bundle has not changed since signing by the corresponding key; it does not prove that every matching database record was included.

## Scenario C: Client Account Access Auditing

    POST /audit/account-access

Example request:

    {
      "actorId": "employee_123",
      "accountId": "account_456",
      "action": "VIEW",
      "outcome": "DENIED",
      "justification": "Insufficient permissions"
    }

The endpoint records allowed and denied access attempts in the existing audit chain.

The calling system supplies the access decision. This service does not authenticate the actor, authorize the access, or independently guarantee that all access attempts are reported.

## Testing

Run:

    python -m pytest -q

The current development milestone has 42 passing automated tests.

Tests generate temporary signing keys and do not require the developer's local private key.

## Engineering Documentation

- `docs/engineering-decisions.md`
- `docs/ai-usage-log.md`
- `ATTESTATION.md`

## Security and Compliance Limitations

This is an engineering prototype, not a production-ready regulatory compliance system.

- No authentication, authorization, or rate limiting
- No externally trusted hash checkpoint or immutable storage
- Privileged attackers could rewrite the chain and recompute hashes
- Tail deletion may go undetected
- Export signatures authenticate bundle contents but do not prove completeness
- Verification and export retrieval do not share a guaranteed consistent snapshot
- Logical archival does not delete or physically separate records
- Redaction does not erase original values from SQLite
- Account-access events depend on accurate reporting by the calling system
- Signing keys require secure lifecycle management in production
- Timestamp boundary handling and operational monitoring need hardening

See `docs/engineering-decisions.md` for the design rationale and outstanding requirements.
