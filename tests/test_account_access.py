from fastapi.testclient import TestClient

from app import database
from app.main import app


def test_allowed_account_access(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "allowed.db"
    )

    with TestClient(app) as client:
        response = client.post(
            "/audit/account-access",
            json={
                "actorId": "employee_123",
                "accountId": "account_456",
                "action": "VIEW",
                "outcome": "ALLOWED",
                "justification": "Customer support request",
            },
        )

        assert response.status_code == 201

        records = client.get(
            "/audit", params={"actorId": "employee_123"}
        ).json()

        assert len(records["events"]) == 1
        assert records["events"][0]["eventType"] == "CLIENT_ACCOUNT_ACCESS"
        assert records["events"][0]["payload"]["outcome"] == "ALLOWED"


def test_denied_account_access(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "denied.db"
    )

    with TestClient(app) as client:
        response = client.post(
            "/audit/account-access",
            json={
                "actorId": "employee_999",
                "accountId": "account_456",
                "action": "VIEW",
                "outcome": "DENIED",
            },
        )

        assert response.status_code == 201
        assert client.get("/audit/verify").json()["valid"] is True


def test_invalid_access_outcome(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "invalid.db"
    )

    with TestClient(app) as client:
        response = client.post(
            "/audit/account-access",
            json={
                "actorId": "employee_123",
                "accountId": "account_456",
                "action": "VIEW",
                "outcome": "UNKNOWN",
            },
        )

        assert response.status_code == 422


def test_missing_account_id(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database, "DATABASE_PATH", tmp_path / "missing.db"
    )

    with TestClient(app) as client:
        response = client.post(
            "/audit/account-access",
            json={
                "actorId": "employee_123",
                "action": "VIEW",
                "outcome": "ALLOWED",
            },
        )

        assert response.status_code == 422
