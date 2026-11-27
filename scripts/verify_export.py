import argparse
import json
import sys
from pathlib import Path

from app.signing_service import verify_signed_bundle


def main():
    parser = argparse.ArgumentParser(
        description="Verify a signed audit export offline."
    )
    parser.add_argument("export_file", type=Path)
    parser.add_argument("public_key_file", type=Path)
    args = parser.parse_args()

    try:
        export = json.loads(
            args.export_file.read_text(encoding="utf-8")
        )
        public_key = args.public_key_file.read_text(
            encoding="utf-8"
        )

        if "signedBundle" in export:
            signed_bundle = export["signedBundle"]

            if not isinstance(signed_bundle, dict):
                raise ValueError("Invalid signedBundle")

            bundle = signed_bundle.get("bundle")

            if not isinstance(bundle, dict):
                raise ValueError("Invalid bundle")

            for field, value in bundle.items():
                if field not in export or export[field] != value:
                    raise ValueError(
                        f"Unsigned outer field mismatch: {field}"
                    )

            allowed_fields = set(bundle) | {"signedBundle"}
            if set(export) != allowed_fields:
                raise ValueError("Unexpected unsigned export fields")
        else:
            signed_bundle = export

        valid = verify_signed_bundle(
            signed_bundle,
            public_key,
        )

    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(f"Verification error: {error}")
        return 2

    if valid:
        print("VALID: Export signature verified.")
        return 0

    print("INVALID: Export signature verification failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
