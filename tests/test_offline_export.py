import json
import subprocess
import sys
from pathlib import Path

from app import signing_service


def test_offline_export_verification(tmp_path, monkeypatch):
    key_path = tmp_path / "signing_key.pem"
    monkeypatch.setattr(
        signing_service, "PRIVATE_KEY_PATH", key_path
    )

    signing_service.generate_signing_key()

    bundle = {
        "exported": True,
        "filters": {"actorId": "employee_123"},
        "total": 1,
        "events": [
            {"id": 1, "payload": {"action": "VIEW"}}
        ],
    }

    signed = signing_service.sign_bundle(bundle)
    export = {**bundle, "signedBundle": signed}

    export_path = tmp_path / "export.json"
    public_key_path = tmp_path / "public_key.pem"

    export_path.write_text(json.dumps(export))
    public_key_path.write_text(
        signing_service.public_key_pem()
    )

    project_root = Path(__file__).resolve().parents[1]

    command = [
        sys.executable,
        "-m",
        "scripts.verify_export",
        str(export_path),
        str(public_key_path),
    ]

    valid = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert valid.returncode == 0, valid.stderr
    assert "VALID" in valid.stdout

    # Modify the outer export without changing the signed bundle.
    export["events"][0]["payload"]["action"] = "DELETE"
    export_path.write_text(json.dumps(export))

    tampered = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    assert tampered.returncode != 0
