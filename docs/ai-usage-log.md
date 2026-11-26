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
