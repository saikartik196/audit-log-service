import pytest

from app import signing_service


@pytest.fixture(autouse=True)
def isolated_signing_key(tmp_path, monkeypatch):
    key_path = tmp_path / "automatic_test_key.pem"

    monkeypatch.setattr(
        signing_service,
        "PRIVATE_KEY_PATH",
        key_path,
    )

    signing_service.generate_signing_key()
