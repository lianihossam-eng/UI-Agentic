"""Independent checker for the Trusted Verification Kernel attested by LOCKED.

Runs after the current-run provenance checker. It recomputes every kernel file
from the checkout, verifies the per-file manifest embedded in the attestation,
and revalidates the attestation's full SHA-256 digest.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.trust_kernel import trusted_kernel_digest, trusted_kernel_manifest


def fail(message: str) -> None:
    print(f"STRICT KERNEL FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"cannot read {path.relative_to(BASE)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must be an object")
    return value


def sha256_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def main() -> int:
    attestation = load(BASE / ".goal_attestation.json")
    if attestation.get("verdict") != "LOCKED":
        fail("attestation is not LOCKED")
    payload = attestation.get("attestation") or {}
    if payload.get("attestation_version") != "2.2":
        fail("attestation does not use runtime+kernel-bound v2.2 format")
    if not payload.get("runtime_identity_root"):
        fail("attestation v2.2 missing runtime_identity_root")

    actual_manifest = trusted_kernel_manifest(BASE)
    actual_digest = trusted_kernel_digest(BASE)
    if payload.get("trusted_kernel_digest") != actual_digest:
        fail("trusted kernel digest mismatch")
    if payload.get("trusted_kernel_manifest") != actual_manifest:
        fail("trusted kernel per-file manifest mismatch")

    artifact_manifest = load(BASE / "reports" / "trusted_kernel_manifest.json")
    if artifact_manifest.get("algorithm") != "sha256":
        fail("trusted kernel artifact algorithm mismatch")
    if artifact_manifest.get("trusted_kernel_digest") != actual_digest:
        fail("trusted kernel artifact digest mismatch")
    if artifact_manifest.get("files") != actual_manifest:
        fail("trusted kernel artifact file manifest mismatch")

    expected_attestation_digest = sha256_json(payload)
    if attestation.get("digest_algo") != "sha256":
        fail("attestation digest algorithm mismatch")
    if attestation.get("digest") != expected_attestation_digest:
        fail("attestation payload digest mismatch")

    print(
        "STRICT KERNEL PASS",
        json.dumps(
            {
                "trusted_kernel_digest": actual_digest,
                "files": len(actual_manifest),
                "runtime_identity_root": payload["runtime_identity_root"],
                "attestation_digest": expected_attestation_digest,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
