"""Finalize an attestation from the exact current-run proof bundle.

Must run only after run_goal_verify.py and the pre-attestation gate have passed.
The resulting attestation binds the current commit, environment, report root,
visual snapshot, Evidence DAG root, measurement kernel, runtime binaries/fonts
and complete Trusted Verification Kernel.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.measurement_kernel import measurement_kernel_digest
from core.trust_kernel import trusted_kernel_digest, trusted_kernel_manifest

REPORT_DIR = BASE / "reports"
REPORT_NAMES = [
    "traceability_report",
    "assumptions_report",
    "parent_contract_report",
    "cross_layer_report",
    "visual_review",
    "regression_report",
    "mutation_report",
]


def fail(message: str):
    print(f"FINALIZE ATTESTATION FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def sha256_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def sha16_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE).decode().strip()


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} must be a JSON object")
    return value


def main() -> int:
    result = load(REPORT_DIR / "final_result.json")
    gate = result.get("final_gate") or {}
    if gate.get("passed") is not True or gate.get("blocking_gates"):
        fail("run_goal_verify final gate is not closed")

    manifest = load(REPORT_DIR / "environment_manifest.json")
    commit = current_commit()
    if manifest.get("commit_sha") != commit:
        fail("environment manifest is not bound to current commit")
    if manifest.get("github_run_id") not in (os.environ.get("GITHUB_RUN_ID"), "local"):
        fail("environment manifest run id does not match this job")
    if manifest.get("evidence_root") != result.get("evidence_root"):
        fail("environment manifest evidence root != final result")

    measurement_root = measurement_kernel_digest()
    if manifest.get("measurement_kernel_digest") != measurement_root:
        fail("environment manifest measurement kernel mismatch")
    if result.get("measurement_kernel_digest") != measurement_root:
        fail("final result measurement kernel mismatch")

    report_hashes = {}
    for name in REPORT_NAMES:
        report = load(REPORT_DIR / f"{name}.json")
        if report.get("generation_mode") != "current-run":
            fail(f"{name} was not generated from current run")
        if report.get("commit_sha") != commit:
            fail(f"{name} commit mismatch")
        if report.get("environment_manifest_digest") != manifest.get("manifest_digest"):
            fail(f"{name} environment manifest mismatch")
        if report.get("evidence_root") != result.get("evidence_root"):
            fail(f"{name} evidence root mismatch")
        report_hash = report.get("report_hash")
        if not report_hash:
            fail(f"{name} missing report hash")
        report_hashes[name] = report_hash

    reports_root = sha256_json(report_hashes)
    visual = load(REPORT_DIR / "visual_review.json")
    visual_root = visual.get("snapshot_digest")
    if visual.get("verdict") != "ACCEPTED" or visual.get("status") != "PASS":
        fail("visual acceptance is not ACCEPTED")
    if not visual_root:
        fail("visual review missing snapshot digest")

    current_run = load(REPORT_DIR / "current_run_evidence.json")
    if current_run.get("evidence_root") != result.get("evidence_root"):
        fail("current_run_evidence root mismatch")
    if current_run.get("visual_snapshot_digest") != visual_root:
        fail("current_run_evidence visual snapshot mismatch")
    if current_run.get("measurement_kernel_digest") != measurement_root:
        fail("current_run_evidence measurement kernel mismatch")

    runtime = load(REPORT_DIR / "runtime_identity.json")
    runtime_payload = {
        key: value
        for key, value in runtime.items()
        if key not in ("report_hash", "report_hash_algo")
    }
    if not runtime.get("report_hash") or sha16_json(runtime_payload) != runtime.get("report_hash"):
        fail("runtime_identity report hash mismatch")
    if runtime.get("generation_mode") != "current-run" or runtime.get("status") != "PASS":
        fail("runtime_identity is not current-run PASS")
    current_binding = current_run.get("binding") or {}
    for field in (
        "commit_sha",
        "scenario_digest",
        "rules_digest",
        "checker_digest",
        "environment_manifest_digest",
        "evidence_root",
    ):
        if runtime.get(field) != current_binding.get(field):
            fail(f"runtime_identity binding mismatch: {field}")
    runtime_root = runtime.get("runtime_identity_root")
    if not runtime_root:
        fail("runtime_identity_root missing")

    kernel_manifest = trusted_kernel_manifest(BASE)
    kernel_digest = trusted_kernel_digest(BASE)
    kernel_manifest_path = REPORT_DIR / "trusted_kernel_manifest.json"
    kernel_manifest_path.write_text(
        json.dumps(
            {
                "trusted_kernel_digest": kernel_digest,
                "algorithm": "sha256",
                "files": kernel_manifest,
            },
            indent=2,
            sort_keys=True,
        )
    )

    payload = {
        "attestation_version": "2.3",
        "subject": {"commit_sha": commit, "build_digest": commit},
        "contract": "public-audit-contract-v2",
        "scenario_digest": manifest.get("scenario_digest"),
        "rules_digest": manifest.get("rules_digest"),
        "checker_digest": manifest.get("checker_digest"),
        "measurement_kernel_digest": measurement_root,
        "trusted_kernel_digest": kernel_digest,
        "trusted_kernel_manifest": kernel_manifest,
        "environment_manifest_digest": manifest.get("manifest_digest"),
        "runtime_identity_root": runtime_root,
        "evidence_root": result.get("evidence_root"),
        "reports_root": reports_root,
        "report_hashes": report_hashes,
        "visual_evidence_root": visual_root,
        "visual_reviewer": visual.get("reviewer"),
        "source_run_id": manifest.get("github_run_id"),
        "browser": result.get("browser"),
        "coverage": result.get("coverage"),
        "final_gate": gate,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    digest = sha256_json(payload)
    attestation = {
        "attestation": payload,
        "digest": digest,
        "digest_algo": "sha256",
        "verdict": "LOCKED",
    }
    (BASE / ".goal_attestation.json").write_text(
        json.dumps(attestation, indent=2, sort_keys=True)
    )
    print(
        "FINAL ATTESTATION LOCKED",
        json.dumps(
            {
                "digest": digest,
                "commit_sha": commit,
                "evidence_root": payload["evidence_root"],
                "measurement_kernel_digest": measurement_root,
                "reports_root": reports_root,
                "visual_evidence_root": visual_root,
                "runtime_identity_root": runtime_root,
                "trusted_kernel_digest": kernel_digest,
                "source_run_id": payload["source_run_id"],
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
