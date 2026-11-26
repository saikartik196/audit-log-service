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
