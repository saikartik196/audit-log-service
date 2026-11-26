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


def test_detects_database_tampering(client):
    # Create a legitimate audit event.
    response = client.post(
        "/audit",
        json=make_event("ACCOUNT_UPDATED"),
    )
    assert response.status_code == 201

    # Verify the original record.
    before = client.get("/audit/verify")
    assert before.status_code == 200
    assert before.json()["valid"] is True

    # Simulate an attacker directly changing the database.
    with database.get_connection() as connection:
        connection.execute(
            """
            UPDATE audit_events
            SET actor_id = ?
            WHERE id = ?
            """,
            ("attacker_999", 1),
        )
        connection.commit()

    # The verification endpoint must detect the alteration.
    after = client.get("/audit/verify")

    assert after.status_code == 200
    assert after.json()["valid"] is False
    assert after.json()["failedEventId"] == 1
    assert after.json()["reason"] == "Content hash mismatch"


def test_detects_broken_hash_link(client):
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

    # Tamper with the second event's predecessor reference.
    with database.get_connection() as connection:
        connection.execute(
            """
            UPDATE audit_events
            SET previous_hash = ?
            WHERE id = ?
            """,
            ("fake_previous_hash", 2),
        )
        connection.commit()

    response = client.get("/audit/verify")

    assert response.status_code == 200

    result = response.json()

    assert result["valid"] is False
    assert result["failedEventId"] == 2
    assert result["reason"] == "Previous hash mismatch"


def test_filter_events_by_actor(client):
    client.post("/audit", json=make_event("USER_LOGIN"))

    second_event = make_event("ACCOUNT_UPDATED")
    second_event["actorId"] = "employee_999"

    client.post("/audit", json=second_event)

    response = client.get(
        "/audit",
        params={"actorId": "employee_999"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["actorId"] == "employee_999"


def test_filter_events_by_event_type(client):
    client.post("/audit", json=make_event("USER_LOGIN"))
    client.post("/audit", json=make_event("ACCOUNT_UPDATED"))

    response = client.get(
        "/audit",
        params={"eventType": "ACCOUNT_UPDATED"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["events"][0]["eventType"] == "ACCOUNT_UPDATED"


def test_audit_pagination(client):
    for _ in range(5):
        response = client.post(
            "/audit",
            json=make_event(),
        )
        assert response.status_code == 201

    response = client.get(
        "/audit",
        params={"limit": 2, "offset": 2},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2
    assert len(data["events"]) == 2
    assert [event["id"] for event in data["events"]] == [3, 4]


def test_invalid_pagination_is_rejected(client):
    response = client.get(
        "/audit",
        params={"limit": 0},
    )

    assert response.status_code == 422


def test_filter_by_resource(client):
    first = make_event("ACCOUNT_VIEWED")
    first["resourceId"] = "account_111"

    second = make_event("ACCOUNT_VIEWED")
    second["resourceId"] = "account_222"

    client.post("/audit", json=first)
    client.post("/audit", json=second)

    response = client.get(
        "/audit",
        params={
            "resourceType": "ACCOUNT",
            "resourceId": "account_222",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["events"][0]["resourceId"] == "account_222"


def test_filter_by_time_range(client):
    for date in [
        "2026-01-01T10:00:00Z",
        "2026-02-01T10:00:00Z",
        "2026-03-01T10:00:00Z",
    ]:
        event = make_event()
        event["timestamp"] = date
        assert client.post("/audit", json=event).status_code == 201

    response = client.get(
        "/audit",
        params={
            "startTime": "2026-01-15T00:00:00Z",
            "endTime": "2026-02-15T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["events"][0]["timestamp"].startswith(
        "2026-02-01"
    )


def test_naive_timestamp_is_interpreted_as_utc(client):
    event = make_event()
    event["timestamp"] = "2026-02-01T10:00:00"

    response = client.post("/audit", json=event)

    assert response.status_code == 201
    assert response.json()["timestamp"] == "2026-02-01T10:00:00+00:00"


def test_query_preserves_original_payload(client):
    event = make_event()
    event["payload"] = {
        "action": "VIEW",
        "metadata": {"source": "dashboard"},
    }

    assert client.post("/audit", json=event).status_code == 201

    response = client.get("/audit")

    assert response.status_code == 200
    assert response.json()["events"][0]["payload"] == event["payload"]
