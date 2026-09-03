"""Deterministic Final Confirmation Gate over the exact current-run bundle.

All browser measurements are produced by core.replay_engine during
capture_current_run_evidence.py. This verifier never replays the UI; it validates
that exact evidence, its current-run bindings and the independent strict gates.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import yaml

from core.attestation import attest
from core.coverage import CoverageLedger, final_confirmation_gate
from core.scenario_compiler import compile as compile_scenarios

BASE = pathlib.Path(__file__).resolve().parent
REPORT_DIR = BASE / "reports"
DOMAIN = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
SCENARIOS = compile_scenarios(DOMAIN)
RULES_SEED = [
    "group.uniform_gap",
    "global.spacing.scale",
    "breakpoint.shell.direction",
    "paint.contrast.text",
    "component.button.hit-target",
    "TARGET_OPERABLE",
    "accessibility.focus-order",
    "FOCUS_USABLE",
    "temporal.geometry-stable",
    "MODAL_INTEGRITY",
]
CHECKER_FILES = [
    "gvh/verify.py",
    "gvh/extractor.py",
    "core/coverage.py",
    "core/scenario_compiler.py",
]
REPORT_NAMES = (
    "traceability_report",
    "assumptions_report",
    "parent_contract_report",
    "cross_layer_report",
    "visual_review",
    "regression_report",
    "mutation_report",
)
BINDING_FIELDS = (
    "commit_sha",
    "scenario_digest",
    "rules_digest",
    "checker_digest",
    "environment_manifest_digest",
    "evidence_root",
)


def sha16_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError(f"cannot read {path.relative_to(BASE)}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{path.relative_to(BASE)} must be an object")
    return value


def report_hash_valid(report: dict) -> bool:
    expected = report.get("report_hash")
    if not expected:
        return False
    payload = {key: value for key, value in report.items() if key not in ("report_hash", "report_hash_algo")}
    return sha16_json(payload) == expected


def run_gate(script: str) -> tuple[bool, str, str]:
    result = subprocess.run(
        [sys.executable, str(BASE / "scripts" / script)],
        cwd=BASE,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE).decode().strip()


def main() -> int:
    try:
        current = load(REPORT_DIR / "current_run_evidence.json")
        manifest = load(REPORT_DIR / "environment_manifest.json")
    except RuntimeError as exc:
        print(f"NO LOCK: {exc}", file=sys.stderr)
        return 2

    scenario_digest = sha16_json(SCENARIOS)
    rules_digest = hashlib.sha256(
        (BASE / "supported-domain.yaml").read_bytes()
        + json.dumps(RULES_SEED, sort_keys=True).encode()
    ).hexdigest()[:16]
    checker_digest = hashlib.sha256(
        b"".join((BASE / path).read_bytes() for path in CHECKER_FILES)
    ).hexdigest()[:16]
    manifest_payload = {
        key: value for key, value in manifest.items()
        if key not in ("manifest_digest", "manifest_hash_algo")
    }
    manifest_digest = sha16_json(manifest_payload)
    commit = current_commit()

    expected_binding = {
        "commit_sha": commit,
        "scenario_digest": scenario_digest,
        "rules_digest": rules_digest,
        "checker_digest": checker_digest,
        "environment_manifest_digest": manifest_digest,
        "evidence_root": current.get("evidence_root"),
    }
    binding = current.get("binding") or {}
    binding_valid = binding == expected_binding
    manifest_valid = (
        manifest.get("manifest_digest") == manifest_digest
        and manifest.get("commit_sha") == commit
        and manifest.get("github_sha") == commit
        and manifest.get("scenario_digest") == scenario_digest
        and manifest.get("rules_digest") == rules_digest
        and manifest.get("checker_digest") == checker_digest
        and manifest.get("evidence_root") == current.get("evidence_root")
        and current.get("environment_manifest_digest") == manifest_digest
    )

    artifact = dict(current)
    artifact_hash = artifact.pop("artifact_hash", None)
    artifact_hash_valid = bool(artifact_hash) and artifact_hash == sha16_json(artifact)

    records = current.get("records")
    if not isinstance(records, list):
        records = []
    ledger = CoverageLedger(SCENARIOS)
    for record in records:
        result = record.get("result") if isinstance(record, dict) else None
        ledger.record(result if isinstance(result, dict) else {"status": "UNKNOWN"})

    reports = {}
    reports_valid = binding_valid and manifest_valid and artifact_hash_valid
    for name in REPORT_NAMES:
        try:
            report = load(REPORT_DIR / f"{name}.json")
        except RuntimeError:
            reports_valid = False
            continue
        reports[name] = report
        if not report_hash_valid(report):
            reports_valid = False
        if report.get("generation_mode") != "current-run":
            reports_valid = False
        for field in BINDING_FIELDS:
            if report.get(field) != expected_binding[field]:
                reports_valid = False

    strict_obligation_ok, strict_obligation_out, strict_obligation_err = run_gate("strict_obligation_gate.py")
    strict_mutation_ok, strict_mutation_out, strict_mutation_err = run_gate("strict_mutation_gate.py")
    strict_visual_ok, strict_visual_out, strict_visual_err = run_gate("strict_visual_gate.py")
    strict_runtime_ok, strict_runtime_out, strict_runtime_err = run_gate("strict_runtime_identity_gate.py")

    readiness_complete = (
        len(records) == len(SCENARIOS)
        and all(record.get("readiness_status") == "PASS" for record in records)
    )

    records_by_id = {
        (record.get("scenario") or {}).get("scenario_id"): record
        for record in records
        if isinstance(record, dict)
    }
    transition_ids = {
        scenario["scenario_id"] for scenario in SCENARIOS
        if scenario["rule"].startswith("transition:")
    }
    state_transitions_complete = bool(transition_ids) and all(
        scenario_id in records_by_id
        and (records_by_id[scenario_id].get("result") or {}).get("status") == "PASS"
        for scenario_id in transition_ids
    )

    assumptions = reports.get("assumptions_report", {})
    unstated_assumptions_zero = (
        reports_valid
        and assumptions.get("status") == "PASS"
        and assumptions.get("unstated_count") == 0
    )

    regression = reports.get("regression_report", {})
    regression_closed = (
        reports_valid
        and regression.get("status") == "PASS"
        and regression.get("closed") is True
        and regression.get("run_a_evidence_root") == current.get("evidence_root")
        and regression.get("run_b_evidence_root") == current.get("evidence_root")
        and (current.get("reproducibility") or {}).get("passed") is True
    )

    parent = reports.get("parent_contract_report", {})
    parent_contracts_valid = (
        reports_valid
        and parent.get("status") == "PASS"
        and parent.get("all_valid") is True
    )

    cross = reports.get("cross_layer_report", {})
    cross_layer_invariants_complete = (
        reports_valid
        and cross.get("status") == "PASS"
        and cross.get("complete") is True
        and (cross.get("snapshot_evidence") or {}).get("all_pass") is True
    )

    gate_checks = {
        "requirement_traceability": reports_valid and strict_obligation_ok,
        "required_proof_levels": reports_valid and strict_obligation_ok,
        "certificate_validation": reports_valid and strict_obligation_ok,
        "measurement_readiness": readiness_complete,
        "critical_mutants_zero": reports_valid and strict_mutation_ok,
        "unstated_assumptions_zero": unstated_assumptions_zero,
        "regression_closed": regression_closed,
        "parent_contracts_valid": parent_contracts_valid,
        "state_transitions_complete": state_transitions_complete,
        "cross_layer_invariants_complete": cross_layer_invariants_complete,
        "compliance_obligations_complete": not bool(DOMAIN.get("compliance_profiles")),
        "visual_acceptance": reports_valid and strict_visual_ok,
    }
    gate = final_confirmation_gate(ledger, gate_checks)

    report = {
        "supported_domain": DOMAIN,
        "coverage": ledger.summary(),
        "browser": current.get("browser"),
        "evidence_root": current.get("evidence_root"),
        "final_gate": gate,
        "bundle_validation": {
            "binding_valid": binding_valid,
            "manifest_valid": manifest_valid,
            "artifact_hash_valid": artifact_hash_valid,
            "reports_valid": reports_valid,
            "strict_obligation_gate": {
                "passed": strict_obligation_ok,
                "stdout": strict_obligation_out,
                "stderr": strict_obligation_err,
            },
            "strict_mutation_gate": {
                "passed": strict_mutation_ok,
                "stdout": strict_mutation_out,
                "stderr": strict_mutation_err,
            },
            "strict_visual_gate": {
                "passed": strict_visual_ok,
                "stdout": strict_visual_out,
                "stderr": strict_visual_err,
            },
            "strict_runtime_identity_gate": {
                "passed": strict_runtime_ok,
                "stdout": strict_runtime_out,
                "stderr": strict_runtime_err,
            },
        },
    }
    # Runtime identity is a pre-attestation prerequisite even though the
    # canonical Final Gate list predates this hardening.
    if not strict_runtime_ok:
        report["final_gate"]["passed"] = False
        report["final_gate"]["blocking_gates"].append("runtime_identity")

    print(json.dumps(report, indent=2, sort_keys=True))

    if report["final_gate"]["passed"]:
        provisional = attest(
            build_digest=commit,
            contract_digest="public-audit-contract-v2",
            rules_digest=rules_digest,
            scenario_digest=scenario_digest,
            evidence_root=current.get("evidence_root"),
            final_gate=report["final_gate"],
            environment_manifest={
                "browser": current.get("browser"),
                "manifest_digest": manifest_digest,
            },
            visual_contract="ACCEPTED",
        )
        (BASE / ".goal_attestation.json").write_text(json.dumps(provisional, indent=2, sort_keys=True))
        return 0

    print("NO LOCK: Final Confirmation Gate is not closed.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
