# Engineering Decisions and Compliance Assumptions

## 1. Project Scope

This project implements a prototype audit logging service with:

- Persistent audit event ingestion
- SHA-256 hash chaining
- Chain integrity verification
- Event filtering and pagination
- Filtered JSON export

The implementation prioritizes a working, testable core over
production-scale infrastructure.

## 2. Architecture

The service uses:

- FastAPI for REST endpoints
- Pydantic for request validation
- SQLite for persistent storage
- SHA-256 for event hash chaining
- pytest for automated testing

Audit events are stored in insertion order using an
auto-incrementing database identifier.

## 3. Integrity Model

Each event contains a content hash and a reference to the
previous event's content hash.

The first event uses GENESIS as its predecessor marker.

Verification recalculates each stored event hash and checks
the predecessor references.

This detects ordinary unauthorized modifications to event
contents and hash links.

However, hash chaining alone does not provide absolute
tamper-proof storage.

A privileged attacker could rewrite records and recompute
their hashes. Deletion of the final record may also remain
undetected without an independently trusted checkpoint.

A production design should periodically publish or securely
store signed chain checkpoints outside the audit database.

## 4. Append-Only Behavior

The public API provides event creation but no update or
delete endpoint.

This is an API-level append-only policy, not a database-level
guarantee. A database administrator can still modify records.

Production enforcement would require restricted database
permissions and additional storage controls.

## 5. Concurrency

Event insertion uses a SQLite BEGIN IMMEDIATE transaction
to serialize writers while selecting the predecessor hash.

This is appropriate for the prototype but does not establish
production scalability.

## 6. Timestamp Assumptions

Events may supply a timestamp or allow the server to generate one.

Timezone-naive client timestamps are interpreted as UTC.

The query API supports start and end timestamps.

Timestamp filtering currently relies on SQLite text comparison.
Boundary handling and canonical timestamp formatting need
additional hardening.

## 7. Export Assumptions

Filtered export supports actor ID and resource ID.

The service verifies the full stored chain before returning
matching events.

This does not independently prove the completeness or
authenticity of an exported subset.

Verification and export retrieval are separate operations,
so they do not currently share a consistent database snapshot.

## 8. Compliance Scenario

Requirement presented:

"Regulators need to be able to audit access to client account data."

### Clarifying Questions

Before production implementation, stakeholders should specify:

1. Which account data and access actions must be recorded?
2. Must unsuccessful access attempts also be logged?
3. Which actor identities and organizational roles are required?
4. What retention period and jurisdiction apply?
5. Which regulators can request or retrieve audit data?
6. What export format and evidence standards are required?
7. Must logs include the legal basis or business purpose for access?
8. Which personal data must be redacted or excluded?
9. What availability and response-time requirements apply?
10. How should unauthorized or missing audit events be detected?

### Working Assumptions

For this prototype:

- ACCOUNT is an example resource type.
- ACCOUNT_VIEWED represents a possible access event.
- actorId identifies the application-reported actor.
- resourceId identifies the accessed account.
- payload may contain structured contextual metadata.
- The application producing events is responsible for
  emitting the relevant access events.

These are assumptions, not confirmed regulatory requirements.

### Current Implementation

The API can ingest ACCOUNT_VIEWED events, search by actor
or resource, and export matching records.

It does not automatically intercept access to client account
data or establish that every access was logged.

### Outstanding Compliance Work

- Authentication and authorization
- Reliable actor identity verification
- Mandatory instrumentation of account access
- Retention and deletion policies
- Privacy-aware redaction
- Independent integrity checkpoints
- Audit access controls and audit-of-audit events
- Regulatory evidence and completeness guarantees

## 9. Scenario B Tradeoffs

Retention and redaction are not implemented in this prototype.

Deleting or modifying an event directly would invalidate
the existing hash chain.

A future design could retain immutable cryptographic
commitments while separately managing encrypted sensitive
payloads under a documented retention policy.

Such a design would require explicit decisions about
privacy, key management, and verification semantics.

## 10. Security and Operational Limitations

This prototype does not provide:

- Authentication or authorization
- Rate limiting
- Independent hash anchoring
- Production monitoring or alerting
- Database backups and recovery
- Guaranteed detection of missing events
- Cryptographically complete filtered exports

These limitations must be addressed before production use.
