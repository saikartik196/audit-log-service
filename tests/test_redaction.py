import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        tmp_path / "redaction_test.db",
    )

    with TestClient(app) as test_client:
        yield test_client


def make_event():
    return {
        "eventType": "ACCOUNT_VIEWED",
        "actorId": "employee_123",
        "resourceType": "ACCOUNT",
        "resourceId": "account_456",
        "payload": {
            "action": "VIEW",
            "customer": {
                "email": "customer@example.com",
                "phone": "1234567890",
            },
        },
    }


def create_event(client):
    response = client.post("/audit", json=make_event())
    assert response.status_code == 201
    return response.json()


def redact(client, field_path):
    return client.post(
        "/audit/1/redact",
        json={"fieldPath": field_path},
    )


def test_redact_nested_field(client):
    create_event(client)

    response = redact(client, "customer.email")
    assert response.status_code == 200

    result = client.get("/audit").json()
    payload = result["events"][0]["payload"]

    assert payload["customer"]["email"] == "[REDACTED]"
    assert payload["customer"]["phone"] == "1234567890"


def test_redaction_preserves_hash_chain(client):
    original = create_event(client)

    before = client.get("/audit/verify").json()
    assert before["valid"] is True

    assert redact(client, "customer.email").status_code == 200

    after = client.get("/audit/verify").json()
    assert after["valid"] is True

    queried = client.get("/audit").json()["events"][0]
    assert queried["contentHash"] == original["contentHash"]


def test_redaction_applies_to_export(client):
    create_event(client)
    assert redact(client, "customer.email").status_code == 200

    response = client.get(
        "/audit/export",
        params={"actorId": "employee_123"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["exported"] is True
    assert (
        data["events"][0]["payload"]["customer"]["email"]
        == "[REDACTED]"
    )


def test_redaction_rejects_unknown_event(client):
    response = client.post(
        "/audit/999/redact",
        json={"fieldPath": "customer.email"},
    )

    assert response.status_code == 404


def test_redaction_rejects_invalid_field(client):
    create_event(client)

    response = redact(client, "customer.unknown")

    assert response.status_code == 422


def test_repeated_redaction_is_idempotent(client):
    create_event(client)

    first = redact(client, "customer.email")
    second = redact(client, "customer.email")

    assert first.status_code == 200
    assert second.status_code == 200

    with database.get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM audit_redactions"
        ).fetchone()[0]

    assert count == 1
