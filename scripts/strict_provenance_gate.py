"""Strict provenance gate for the final GitHub CI run.

This checker is intentionally independent from run_goal_verify.py. It refuses a
LOCKED claim unless every external report is explicitly bound to the exact
commit and evidence snapshot executed by the current CI job.

Missing provenance is a failure. A stale commit is a failure. Hash integrity
alone is not sufficient.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import yaml

from core.scenario_compiler import compile as compile_scenarios

BASE = pathlib.Path(__file__).resolve().parent.parent
REPORT_NAMES = [
    "traceability_report",
    "assumptions_report",
    "parent_contract_report",
    "cross_layer_report",
    "visual_review",
    "regression_report",
    "mutation_report",
]
REQUIRED_BINDING_FIELDS = (
    "commit_sha",
    "scenario_digest",
    "rules_digest",
    "checker_digest",
    "environment_manifest_digest",
    "evidence_root",
)
RULES_SEED = [
    "group.uniform_gap",
    "global.spacing.scale",
    "paint.contrast.text",
    "component.button.hit-target",
    "TARGET_OPERABLE",
    "accessibility.focus-order",
    "FOCUS_USABLE",
    "temporal.geometry-stable",
    "MODAL_INTEGRITY",
    "breakpoint.shell.direction",
]
CHECKER_FILES = [
    "gvh/verify.py",
    "gvh/extractor.py",
    "core/coverage.py",
    "core/scenario_compiler.py",
]


def fail(message: str) -> None:
    print(f"STRICT PROVENANCE FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def sha16_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=BASE
        ).decode().strip()
    except Exception as exc:  # pragma: no cover - CI must have git
        fail(f"cannot resolve current commit: {exc}")


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        fail(f"missing file: {path.relative_to(BASE)}")
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        fail(f"invalid JSON {path.relative_to(BASE)}: {exc}")
    if not isinstance(data, dict):
        fail(f"expected object in {path.relative_to(BASE)}")
    return data


def verify_report_hash(name: str, data: dict) -> None:
    expected = data.get("report_hash")
    if not expected:
        fail(f"{name}: missing report_hash")
    payload = {
        k: v for k, v in data.items()
        if k not in ("report_hash", "report_hash_algo")
    }
    computed = sha16_json(payload)
    if computed != expected:
        fail(f"{name}: report_hash mismatch {computed} != {expected}")


def main() -> int:
    commit = current_commit()

    domain = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
    scenarios = compile_scenarios(domain)
    scenario_digest = sha16_json(scenarios)
    rules_digest = hashlib.sha256(
        (BASE / "supported-domain.yaml").read_bytes()
        + json.dumps(RULES_SEED, sort_keys=True).encode()
    ).hexdigest()[:16]
    checker_digest = hashlib.sha256(
        b"".join((BASE / path).read_bytes() for path in CHECKER_FILES)
    ).hexdigest()[:16]

    manifest_path = BASE / "reports" / "environment_manifest.json"
    manifest = load_json(manifest_path)
    manifest_payload = {
        k: v for k, v in manifest.items()
        if k not in ("manifest_digest", "manifest_hash_algo")
    }
    manifest_digest = sha16_json(manifest_payload)
    if manifest.get("manifest_digest") != manifest_digest:
        fail(
            "environment_manifest.json: manifest digest mismatch "
            f"{manifest_digest} != {manifest.get('manifest_digest')}"
        )
    if manifest.get("commit_sha") != commit:
        fail(
            "environment_manifest.json: commit_sha is stale "
            f"{manifest.get('commit_sha')} != {commit}"
        )
    if manifest.get("scenario_digest") != scenario_digest:
        fail("environment_manifest.json: scenario_digest does not match current compiler output")
    if manifest.get("rules_digest") != rules_digest:
        fail("environment_manifest.json: rules_digest does not match current rules")
    if manifest.get("checker_digest") != checker_digest:
        fail("environment_manifest.json: checker_digest does not match current checker code")

    attestation = load_json(BASE / ".goal_attestation.json")
    if attestation.get("verdict") != "LOCKED":
        fail(".goal_attestation.json is not LOCKED")
    att = attestation.get("attestation") or {}
    final_gate = att.get("final_gate") or {}
    if final_gate.get("passed") is not True or final_gate.get("blocking_gates"):
        fail("attestation final gate is not closed")
    evidence_root = att.get("evidence_root")
    if not evidence_root:
        fail("attestation missing evidence_root")

    expected_binding = {
        "commit_sha": commit,
        "scenario_digest": scenario_digest,
        "rules_digest": rules_digest,
        "checker_digest": checker_digest,
        "environment_manifest_digest": manifest_digest,
        "evidence_root": evidence_root,
    }

    for name in REPORT_NAMES:
        data = load_json(BASE / "reports" / f"{name}.json")
        verify_report_hash(name, data)
        for field in REQUIRED_BINDING_FIELDS:
            if field not in data:
                fail(f"{name}: missing mandatory binding field {field}")
            if data.get(field) != expected_binding[field]:
                fail(
                    f"{name}: binding mismatch {field}: "
                    f"{data.get(field)} != {expected_binding[field]}"
                )

    print(
        "STRICT PROVENANCE PASS",
        json.dumps(
            {
                "commit_sha": commit,
                "scenario_digest": scenario_digest,
                "rules_digest": rules_digest,
                "checker_digest": checker_digest,
                "environment_manifest_digest": manifest_digest,
                "evidence_root": evidence_root,
                "reports": len(REPORT_NAMES),
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
