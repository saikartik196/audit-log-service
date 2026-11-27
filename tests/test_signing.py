import copy

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from app import signing_service


@pytest.fixture
def signing_keys(tmp_path, monkeypatch):
    key_path = tmp_path / "test_signing_key.pem"
    monkeypatch.setattr(signing_service, "PRIVATE_KEY_PATH", key_path)

    signing_service.generate_signing_key()

    return signing_service.public_key_pem()


def sample_bundle():
    return {
        "exported": True,
        "filters": {"actorId": "employee_123"},
        "total": 1,
        "events": [
            {
                "id": 1,
                "payload": {"action": "VIEW"},
            }
        ],
    }


def test_generated_key_has_restricted_permissions(signing_keys):
    import stat

    permissions = stat.S_IMODE(
        signing_service.PRIVATE_KEY_PATH.stat().st_mode
    )
    assert permissions == 0o600


def test_valid_signature_is_accepted(signing_keys):
    signed = signing_service.sign_bundle(sample_bundle())

    assert signing_service.verify_signed_bundle(
        signed, signing_keys
    )


def test_modified_event_is_rejected(signing_keys):
    signed = signing_service.sign_bundle(sample_bundle())

    tampered = copy.deepcopy(signed)
    tampered["bundle"]["events"][0]["payload"]["action"] = "DELETE"

    assert not signing_service.verify_signed_bundle(
        tampered, signing_keys
    )


def test_modified_filter_is_rejected(signing_keys):
    signed = signing_service.sign_bundle(sample_bundle())

    tampered = copy.deepcopy(signed)
    tampered["bundle"]["filters"]["actorId"] = "attacker"

    assert not signing_service.verify_signed_bundle(
        tampered, signing_keys
    )


def test_wrong_public_key_is_rejected(signing_keys):
    signed = signing_service.sign_bundle(sample_bundle())

    other_key = Ed25519PrivateKey.generate()
    other_public_key = other_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")

    assert not signing_service.verify_signed_bundle(
        signed, other_public_key
    )


def test_duplicate_key_generation_is_rejected(signing_keys):
    with pytest.raises(FileExistsError):
        signing_service.generate_signing_key()
