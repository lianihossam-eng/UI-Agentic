"""Fail-closed verifier for the content-addressed runtime identity."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.runtime_identity import capture_runtime_identity

REPORT_DIR = BASE / "reports"


def fail(message: str) -> None:
    print(f"STRICT RUNTIME IDENTITY FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"cannot read {path.relative_to(BASE)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must be an object")
    return value


def sha16_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    report = load(REPORT_DIR / "runtime_identity.json")
    expected_hash = report.get("report_hash")
    payload = {key: value for key, value in report.items() if key not in ("report_hash", "report_hash_algo")}
    if not expected_hash or sha16_json(payload) != expected_hash:
        fail("runtime identity report hash mismatch")
    if report.get("generation_mode") != "current-run" or report.get("status") != "PASS":
        fail("runtime identity report is not current-run PASS")
    run_id = str(os.environ.get("GITHUB_RUN_ID", "local"))
    if str(report.get("source_run_id")) != run_id:
        fail("runtime identity source_run_id mismatch")

    current = load(REPORT_DIR / "current_run_evidence.json")
    binding = current.get("binding") or {}
    for field in (
        "commit_sha",
        "scenario_digest",
        "rules_digest",
        "checker_digest",
        "environment_manifest_digest",
        "evidence_root",
    ):
        if report.get(field) != binding.get(field):
            fail(f"runtime identity binding mismatch: {field}")

    actual = capture_runtime_identity()
    stable_fields = ("browser", "python", "playwright_version", "fonts", "runtime_identity_root", "runtime_identity_algo")
    for field in stable_fields:
        if report.get(field) != actual.get(field):
            fail(f"runtime identity changed: {field}")

    attestation_path = BASE / ".goal_attestation.json"
    attested = None
    if attestation_path.exists():
        attestation = load(attestation_path)
        if attestation.get("verdict") == "LOCKED":
            attested = (attestation.get("attestation") or {}).get("runtime_identity_root")
            if attested != report.get("runtime_identity_root"):
                fail("LOCKED attestation runtime_identity_root mismatch")

    print(
        "STRICT RUNTIME IDENTITY PASS",
        json.dumps(
            {
                "root": report.get("runtime_identity_root"),
                "browser": report.get("browser", {}).get("version"),
                "browser_sha256": report.get("browser", {}).get("sha256"),
                "python_sha256": report.get("python", {}).get("sha256"),
                "attestation_bound": attested is not None,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
