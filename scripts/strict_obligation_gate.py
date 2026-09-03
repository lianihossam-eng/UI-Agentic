"""Independent fail-closed gate for compiled obligations and traceability.

Validates the freshly compiled Required Scenario Set against current-run records
and the record-bound traceability report. Also derives proof-level and
certificate validity; no literal trust boolean is accepted here.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import yaml

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.attestation import checker as certificate_checker
from core.scenario_compiler import compile as compile_scenarios

REPORT_DIR = BASE / "reports"
PROOF_RANK = {"observed": 1, "bounded": 2, "certified": 3}


def fail(message: str) -> None:
    print(f"STRICT OBLIGATION FAIL: {message}", file=sys.stderr)
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


def verify_report_hash(report: dict) -> None:
    expected = report.get("report_hash")
    if not expected:
        fail("traceability_report missing report_hash")
    payload = {k: v for k, v in report.items() if k not in ("report_hash", "report_hash_algo")}
    if sha16_json(payload) != expected:
        fail("traceability_report hash mismatch")


def main() -> int:
    domain = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
    scenarios = compile_scenarios(domain)
    required = {scenario["scenario_id"]: scenario for scenario in scenarios}
    if len(required) != len(scenarios):
        fail("compiled scenario ids are not unique")

    current = load(REPORT_DIR / "current_run_evidence.json")
    records = current.get("records")
    if not isinstance(records, list) or len(records) != len(required):
        fail("current-run evidence record count mismatch")

    records_by_id = {}
    for record in records:
        scenario = record.get("scenario") or {}
        sid = scenario.get("scenario_id")
        if sid not in required:
            fail(f"unknown evidence scenario_id: {sid}")
        if sid in records_by_id:
            fail(f"duplicate evidence record: {sid}")
        if scenario != required[sid]:
            fail(f"evidence scenario differs from compiled obligation: {sid}")
        result = record.get("result") or {}
        if result.get("constraint") != scenario.get("rule"):
            fail(
                f"result constraint does not match compiled rule: {sid} -> "
                f"{result.get('constraint')} != {scenario.get('rule')}"
            )
        if result.get("status") != "PASS":
            fail(f"required obligation is not PASS: {sid} -> {result.get('status')}")
        if not record.get("evidence_key"):
            fail(f"missing evidence key: {sid}")
        records_by_id[sid] = record

    if set(records_by_id) != set(required):
        fail("current-run evidence does not cover the exact required scenario set")

    trace = load(REPORT_DIR / "traceability_report.json")
    verify_report_hash(trace)
    mapping = trace.get("mapping")
    if not isinstance(mapping, list) or len(mapping) != len(required):
        fail("traceability mapping count mismatch")
    if trace.get("required_obligations") != len(required) or trace.get("traced_obligations") != len(required):
        fail("traceability aggregate counts mismatch")
    if trace.get("percentage") != 100 or trace.get("status") != "PASS":
        fail("traceability report is not 100% PASS")

    mapped = {}
    proof_levels_complete = True
    certificate_required = []
    for item in mapping:
        sid = item.get("scenario_id")
        if sid not in required:
            fail(f"traceability references unknown scenario: {sid}")
        if sid in mapped:
            fail(f"duplicate traceability mapping: {sid}")
        record = records_by_id[sid]
        scenario = required[sid]
        result = record["result"]
        if item.get("rule") != scenario["rule"]:
            fail(f"traceability rule mismatch: {sid}")
        if item.get("evidence_key") != record.get("evidence_key"):
            fail(f"traceability evidence_key mismatch: {sid}")
        if item.get("status") != result.get("status"):
            fail(f"traceability status mismatch: {sid}")
        required_level = scenario.get("required_proof_level", "observed")
        actual_level = result.get("proof_level", "observed")
        if item.get("required_proof_level") != required_level:
            fail(f"traceability required proof level mismatch: {sid}")
        if item.get("evidence_type") != actual_level:
            fail(f"traceability evidence type mismatch: {sid}")
        if required_level not in PROOF_RANK or actual_level not in PROOF_RANK:
            fail(f"unknown proof level: {sid}")
        if PROOF_RANK[actual_level] < PROOF_RANK[required_level]:
            proof_levels_complete = False
        if required_level in ("bounded", "certified"):
            certificate_required.append((sid, result.get("certificate")))
        mapped[sid] = item

    if set(mapped) != set(required):
        fail("traceability does not map the exact required scenario set")
    if not proof_levels_complete:
        fail("one or more obligations do not satisfy their required proof level")

    # Vacuous truth is derived from the compiled requirements. If future
    # obligations require BOUNDED/CERTIFIED, each certificate must pass the
    # independent certificate checker.
    certificate_validation = all(
        certificate is not None and certificate_checker(certificate)
        for _, certificate in certificate_required
    )
    if not certificate_validation:
        fail("required BOUNDED/CERTIFIED certificate validation failed")

    print(
        "STRICT OBLIGATION PASS",
        json.dumps(
            {
                "required": len(required),
                "records": len(records_by_id),
                "trace_mappings": len(mapped),
                "proof_levels_complete": proof_levels_complete,
                "certificate_required": len(certificate_required),
                "certificate_validation": certificate_validation,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
