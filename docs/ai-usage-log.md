# AI Usage Log

## Entry 1 — Initial Project Setup

Date: 2026-11-26

### Task

Initialize a Python REST API project with automated testing.

### AI Assistance

ChatGPT assisted with:

- Selecting Python and FastAPI
- Setting up the virtual environment
- Creating the health check endpoint
- Configuring .gitignore
- Generating an automated health test
- Preparing project documentation

### Developer Actions

- Initialized a local Git repository
- Created the Python virtual environment
- Installed dependencies
- Created and ran the FastAPI application
- Verified the health endpoint in a browser
- Executed the automated test

### Validation

Command:

    python -m pytest -v

Result:

    1 passed, 1 warning

The warning concerns a deprecated test-client integration.

### Engineering Decisions

- FastAPI for REST API implementation
- SQLite planned for lightweight persistence
- Pytest for automated testing
- Git commits after validated milestones

### Limitations

The current implementation only exposes a health endpoint.

Audit event persistence, hash-chain verification,
and security controls remain to be implemented.

## Entry 2 — Audit Event Ingestion

Date: 2026-11-26

### Task

Implement persistent audit event ingestion with SHA-256 hash chaining.

### AI Assistance

ChatGPT assisted with:
- SQLite database schema design
- Pydantic request validation
- Audit event insertion logic
- SHA-256 content hashing
- Transaction handling using BEGIN IMMEDIATE
- FastAPI POST /audit endpoint
- Automated test generation

### Developer Actions

- Created database, schema, and service modules
- Integrated the write endpoint
- Submitted test events through Swagger UI
- Inspected stored records
- Verified linkage between two events
- Ran the automated test suite

### Validation

Command:

    python -m pytest -v

Result:

    5 passed, 1 warning

Verified:
- Successful event creation
- Hash linkage between consecutive events
- Required field validation
- SQLite persistence
- Health endpoint

### Engineering Decisions

- SQLite used for prototype persistence
- SHA-256 used for deterministic event hashing
- BEGIN IMMEDIATE used to serialize competing writers
- GENESIS used as the initial chain predecessor
- Database writes use parameterized SQL

### Known Limitations

- Full hash-chain verification is not implemented
- No tamper-detection endpoint yet
- No query filtering or pagination
- No authentication or authorization
- No retention, redaction, or export
- Current hash design is not independently anchored

## Entry 3 — Hash-Chain Verification and Tamper Detection

Date: 2026-11-26

### Task

Implement independent hash-chain verification and detect direct
modifications to stored audit events.

### AI Assistance

ChatGPT assisted with:
- Designing the hash recalculation function
- Implementing GET /audit/verify
- Checking predecessor hash linkage
- Writing automated database tampering tests
- Identifying limitations of locally stored hash chains

### Developer Actions

- Created app/verification.py
- Integrated the verification endpoint into FastAPI
- Tested verification against two existing audit events
- Ran isolated tests that modified SQLite records directly
- Confirmed detection of altered actor IDs and predecessor hashes

### Validation

Command:

    python -m pytest -v

Result:

    7 passed, 1 warning

Verified:
- Audit event creation and persistence
- Required field validation
- SHA-256 hash linkage
- Detection of modified event content
- Detection of broken predecessor references
- Identification of the affected event

### Known Limitations

- A privileged attacker could recompute and rewrite the entire chain
- Deletion of the final event may go undetected
- No externally trusted hash checkpoint exists
- Query filtering and pagination are not implemented
- Retention, redaction, export, and compliance reporting remain pending

## Entry 4 — Audit Query API

Date: 2026-11-26

### Task

Implement audit event retrieval, filtering, pagination,
and consistent UTC timestamp handling.

### AI Assistance

ChatGPT assisted with:
- Designing the query service
- Building parameterized SQLite filters
- Implementing GET /audit
- Adding pagination validation
- Correcting timezone-naive timestamp handling
- Writing automated query tests

### Developer Actions

- Created app/query_service.py
- Integrated GET /audit into FastAPI
- Tested the API against existing records
- Updated timestamp normalization in app/audit_service.py
- Ran automated tests for filters and pagination

### Validation

Command:

    python -m pytest -v

Result:

    15 passed, 1 warning

Verified:
- Actor and event-type filtering
- Resource type and resource ID filtering
- Time-range filtering for representative timestamps
- Limit and offset pagination
- Rejection of invalid pagination limits
- Preservation of structured payloads
- UTC interpretation of timezone-naive timestamps

### Known Limitations

- Timestamp text comparisons need stronger boundary handling
- No authentication or authorization
- No trusted external hash anchoring
- Retention, redaction, and export are not implemented
- Compliance reporting requirements remain partially specified

## Entry 5 — Filtered Audit Export

Date: 2026-11-26

### Task

Implement JSON export of audit events by actor ID or resource ID.

### AI Assistance

ChatGPT assisted with:
- Designing the export service
- Integrating GET /audit/export
- Implementing batched retrieval
- Adding full-chain verification before export
- Writing automated export tests
- Identifying export integrity limitations

### Developer Actions

- Created app/export_service.py
- Integrated the export endpoint
- Tested export against existing audit records
- Added tests for actor and resource filtering
- Tested export refusal after direct database tampering

### Validation

Command:

    python -m pytest -v

Reported result:

    19 passed

Verified:
- Export requires an actor or resource filter
- Actor-based export
- Resource-based export
- Export includes chain verification status
- Export refuses to return records when chain verification fails

### Known Limitations

- Exported subsets are not independently verifiable
- Export completeness is not cryptographically proven
- Verification and export retrieval are separate database reads
- No authentication or authorization
- No external trusted hash anchor
- Retention and redaction are not implemented
