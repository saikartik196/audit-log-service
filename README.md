# Audit Log Service

A REST API for recording, querying, and verifying audit events.

## Technology Stack

- Python 3.12
- FastAPI
- SQLite (planned)
- Pytest

## Current Features

- FastAPI application
- Health check endpoint
- Automated health endpoint test

## Planned Features

- Append-only audit event storage
- Event filtering and pagination
- Cryptographic hash chaining
- Tamper detection
- Retention and structured redaction
- Verifiable audit export
- Compliance reporting

## Setup

Create a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install -r requirements.txt

## Run the Application

    python -m uvicorn app.main:app --reload

API documentation:

    http://127.0.0.1:8000/docs

Health check:

    http://127.0.0.1:8000/health

## Run Tests

    python -m pytest -v

## Development Process

The application is developed incrementally.

Each milestone includes implementation, validation,
documentation, and a Git commit.

AI assistance is documented separately in docs/ai-usage-log.md.
