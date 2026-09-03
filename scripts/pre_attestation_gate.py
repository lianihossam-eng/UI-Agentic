"""Fail-closed gate that must pass before any authoritative attestation is created.

This checker validates the exact current-run environment, report bindings,
visual evidence and Final Confirmation Gate, but deliberately does not trust or
require .goal_attestation.json. CI must run it before the finalizer.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = BASE / "reports"
REPORT_NAMES = (
    "traceability_report",
    "assumptions_report",
    "parent_contract_report",
    "cross_layer_report",
    "visual_review",
    "regression_report",
    "mutation_report",
)
REQUIRED_BINDINGS = (
    "commit_sha",
    "scenario_digest",
    "rules_digest",
    "checker_digest",
    "environment_manifest_digest",
    "evidence_root",
)


def fail(message: str) -> None:
    print(f"PRE-ATTESTATION FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        fail(f"missing {path.relative_to(BASE)}")
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(BASE)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must be an object")
    return value


def sha16_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def current_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE).decode().strip()
    except Exception as exc:
        fail(f"cannot resolve current commit: {exc}")


def verify_report_hash(name: str, report: dict) -> None:
    expected = report.get("report_hash")
    if not expected:
        fail(f"{name}: missing report_hash")
    payload = {k: v for k, v in report.items() if k not in ("report_hash", "report_hash_algo")}
    if sha16_json(payload) != expected:
        fail(f"{name}: report_hash mismatch")


def main() -> int:
    # The authoritative attestation must not pre-exist this gate. The legacy
    # runner may produce a provisional file; CI deletes it before invoking us.
    if (BASE / ".goal_attestation.json").exists():
        fail("authoritative attestation exists before pre-attestation gate")

    commit = current_commit()
    run_id = str(os.environ.get("GITHUB_RUN_ID", "local"))

    manifest = load(REPORT_DIR / "environment_manifest.json")
    manifest_payload = {
        k: v for k, v in manifest.items()
        if k not in ("manifest_digest", "manifest_hash_algo")
    }
    manifest_digest = sha16_json(manifest_payload)
    if manifest.get("manifest_digest") != manifest_digest:
        fail("environment manifest digest mismatch")
    if manifest.get("generation_mode") != "current-run":
        fail("environment manifest is not current-run generated")
    if manifest.get("commit_sha") != commit or manifest.get("github_sha") != commit:
        fail("environment manifest commit mismatch")
    if str(manifest.get("github_run_id")) != run_id:
        fail("environment manifest run id mismatch")

    current_run = load(REPORT_DIR / "current_run_evidence.json")
    if current_run.get("generation_mode") != "current-run":
        fail("current_run_evidence is not current-run generated")
    if str(current_run.get("source_run_id")) != run_id:
        fail("current_run_evidence run id mismatch")
    if (current_run.get("binding") or {}).get("commit_sha") != commit:
        fail("current_run_evidence commit mismatch")
    if current_run.get("environment_manifest_digest") != manifest_digest:
        fail("current_run_evidence environment mismatch")
    if current_run.get("evidence_root") != manifest.get("evidence_root"):
        fail("current_run_evidence evidence root mismatch")
    reproducibility = current_run.get("reproducibility") or {}
    if reproducibility.get("passed") is not True:
        fail("A/B reproducibility is not proved")

    expected_binding = {
        "commit_sha": commit,
        "scenario_digest": manifest.get("scenario_digest"),
        "rules_digest": manifest.get("rules_digest"),
        "checker_digest": manifest.get("checker_digest"),
        "environment_manifest_digest": manifest_digest,
        "evidence_root": current_run.get("evidence_root"),
    }

    report_hashes = {}
    for name in REPORT_NAMES:
        report = load(REPORT_DIR / f"{name}.json")
        verify_report_hash(name, report)
        if report.get("generation_mode") != "current-run":
            fail(f"{name}: not current-run generated")
        if str(report.get("source_run_id")) != run_id:
            fail(f"{name}: source_run_id mismatch")
        for field in REQUIRED_BINDINGS:
            if field not in report:
                fail(f"{name}: missing mandatory binding {field}")
            if report.get(field) != expected_binding[field]:
                fail(f"{name}: binding mismatch {field}")
        report_hashes[name] = report["report_hash"]

    visual = load(REPORT_DIR / "visual_review.json")
    if visual.get("verdict") != "ACCEPTED" or visual.get("status") != "PASS":
        fail("visual review is not ACCEPTED")
    if not visual.get("reviewer") or visual.get("reviewer_type") != "agent":
        fail("visual reviewer provenance is incomplete")
    if current_run.get("visual_snapshot_digest") != visual.get("snapshot_digest"):
        fail("visual snapshot mismatch")
    if current_run.get("visual_accepted") is not True:
        fail("current_run_evidence does not mark visual accepted")

    final_result = load(REPORT_DIR / "final_result.json")
    gate = final_result.get("final_gate") or {}
    if gate.get("passed") is not True or gate.get("blocking_gates"):
        fail("Final Confirmation Gate is not closed")
    if final_result.get("evidence_root") != current_run.get("evidence_root"):
        fail("final_result evidence root mismatch")
    if final_result.get("browser") != manifest.get("browser"):
        fail("final_result browser mismatch")

    print(
        "PRE-ATTESTATION PASS",
        json.dumps(
            {
                "commit_sha": commit,
                "run_id": run_id,
                "evidence_root": current_run.get("evidence_root"),
                "visual_root": visual.get("snapshot_digest"),
                "reports": len(report_hashes),
                "environment_manifest_digest": manifest_digest,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
