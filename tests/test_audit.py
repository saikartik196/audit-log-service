import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_database = tmp_path / "test_audit.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        test_database,
    )

    with TestClient(app) as test_client:
        yield test_client


def make_event(event_type="USER_LOGIN"):
    return {
        "eventType": event_type,
        "actorId": "user_123",
        "resourceType": "ACCOUNT",
        "resourceId": "account_456",
        "payload": {"result": "SUCCESS"},
    }


def test_create_audit_event(client):
    response = client.post(
        "/audit",
        json=make_event(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["previousHash"] == "GENESIS"
    assert len(data["contentHash"]) == 64


def test_two_events_are_linked(client):
    first = client.post(
        "/audit",
        json=make_event("USER_LOGIN"),
    )

    second = client.post(
        "/audit",
        json=make_event("ACCOUNT_UPDATED"),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_data = first.json()
    second_data = second.json()

    assert (
        second_data["previousHash"]
        == first_data["contentHash"]
    )


def test_missing_required_field_is_rejected(client):
    invalid_event = make_event()
    del invalid_event["actorId"]

    response = client.post(
        "/audit",
        json=invalid_event,
    )

    assert response.status_code == 422


def test_event_is_persisted(client):
    response = client.post(
        "/audit",
        json=make_event(),
    )

    assert response.status_code == 201

    with database.get_connection() as connection:
        row = connection.execute(
            "SELECT event_type FROM audit_events WHERE id = 1"
        ).fetchone()

    assert row is not None
    assert row["event_type"] == "USER_LOGIN"
