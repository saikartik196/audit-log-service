import base64
import json
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


PRIVATE_KEY_PATH = Path(
    os.getenv("AUDIT_SIGNING_KEY_PATH", ".audit_signing_key.pem")
)


def canonical_bytes(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def generate_signing_key():
    if PRIVATE_KEY_PATH.exists():
        raise FileExistsError(
            f"Signing key already exists: {PRIVATE_KEY_PATH}"
        )

    private_key = Ed25519PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Create the private-key file with owner-only permissions.
    fd = os.open(
        PRIVATE_KEY_PATH,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )

    with os.fdopen(fd, "wb") as file:
        file.write(private_bytes)

    return PRIVATE_KEY_PATH


def load_private_key():
    with PRIVATE_KEY_PATH.open("rb") as file:
        private_key = serialization.load_pem_private_key(
            file.read(),
            password=None,
        )

    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("Signing key must be an Ed25519 private key")

    return private_key


def public_key_pem():
    private_key = load_private_key()

    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def sign_bundle(bundle):
    private_key = load_private_key()
    signature = private_key.sign(canonical_bytes(bundle))

    return {
        "bundle": bundle,
        "signatureAlgorithm": "Ed25519",
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def verify_signed_bundle(signed_bundle, trusted_public_key_pem):
    try:
        if signed_bundle["signatureAlgorithm"] != "Ed25519":
            return False

        public_key = serialization.load_pem_public_key(
            trusted_public_key_pem.encode("ascii")
        )

        signature = base64.b64decode(
            signed_bundle["signature"],
            validate=True,
        )

        public_key.verify(
            signature,
            canonical_bytes(signed_bundle["bundle"]),
        )

        return True

    except (KeyError, ValueError, TypeError, InvalidSignature):
        return False
