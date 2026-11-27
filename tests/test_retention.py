from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "retention_test.db",
    )
    monkeypatch.setenv("AUDIT_RETENTION_DAYS", "30")

    with TestClient(app) as test_client:
        yield test_client


def make_event(days_ago):
    timestamp = (
        datetime.now(timezone.utc)
        - timedelta(days=days_ago)
    ).isoformat()

    return {
        "eventType": "ACCOUNT_VIEWED",
        "actorId": "employee_123",
        "resourceType": "ACCOUNT",
        "resourceId": "account_456",
        "payload": {"action": "VIEW"},
        "timestamp": timestamp,
    }


def archived_at_for(event_id):
    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT archived_at FROM audit_events WHERE id = ?",
            (event_id,),
        ).fetchone()
    return row["archived_at"]


def test_old_events_are_archived(client):
    assert client.post(
        "/audit", json=make_event(60)
    ).status_code == 201

    response = client.post("/audit/archive")

    assert response.status_code == 200
    assert response.json()["archivedCount"] == 1
    assert archived_at_for(1) is not None


def test_recent_events_are_not_archived(client):
    assert client.post(
        "/audit", json=make_event(5)
    ).status_code == 201

    response = client.post("/audit/archive")

    assert response.status_code == 200
    assert response.json()["archivedCount"] == 0
    assert archived_at_for(1) is None


def test_archiving_preserves_hash_chain(client):
    assert client.post(
        "/audit", json=make_event(60)
    ).status_code == 201

    assert client.post(
        "/audit", json=make_event(5)
    ).status_code == 201

    before = client.get("/audit/verify")
    assert before.json()["valid"] is True

    assert client.post("/audit/archive").status_code == 200

    after = client.get("/audit/verify")
    assert after.status_code == 200
    assert after.json()["valid"] is True


def test_archiving_is_idempotent(client):
    assert client.post(
        "/audit", json=make_event(60)
    ).status_code == 201

    first = client.post("/audit/archive")
    second = client.post("/audit/archive")

    assert first.json()["archivedCount"] == 1
    assert second.json()["archivedCount"] == 0


def test_retention_window_is_configurable(client, monkeypatch):
    assert client.post(
        "/audit", json=make_event(15)
    ).status_code == 201

    first = client.post("/audit/archive")
    assert first.json()["archivedCount"] == 0

    monkeypatch.setenv("AUDIT_RETENTION_DAYS", "10")

    second = client.post("/audit/archive")

    assert second.json()["archivedCount"] == 1
    assert second.json()["retentionDays"] == 10
    assert archived_at_for(1) is not None
