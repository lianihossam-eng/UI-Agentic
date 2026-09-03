"""Build traceability from the exact current-run evidence records.

This deliberately does not zip the compiler output with execution-order records.
Every mapping is keyed by the canonical scenario_id embedded in the actual
record, then checked against the freshly compiled Required Scenario Set.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

import yaml

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.scenario_compiler import compile as compile_scenarios

REPORT_DIR = BASE / "reports"


def fail(message: str) -> None:
    print(f"TRACEABILITY BUILD FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"cannot read {path.relative_to(BASE)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must be a JSON object")
    return value


def sha16_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    domain = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
    scenarios = compile_scenarios(domain)
    required = {scenario["scenario_id"]: scenario for scenario in scenarios}
    if len(required) != len(scenarios):
        fail("compiled scenario ids are not unique")

    current = load(REPORT_DIR / "current_run_evidence.json")
    if current.get("generation_mode") != "current-run":
        fail("current_run_evidence is not current-run generated")
    run_id = str(os.environ.get("GITHUB_RUN_ID", "local"))
    if str(current.get("source_run_id")) != run_id:
        fail("current_run_evidence source_run_id mismatch")

    records = current.get("records")
    if not isinstance(records, list) or len(records) != len(scenarios):
        fail(f"record count {len(records) if isinstance(records, list) else 'invalid'} != required {len(scenarios)}")

    by_id = {}
    mapping = []
    for record in records:
        scenario = record.get("scenario") or {}
        sid = scenario.get("scenario_id")
        if not sid or sid not in required:
            fail(f"record has unknown/missing scenario_id: {sid}")
        if sid in by_id:
            fail(f"duplicate evidence record for {sid}")
        if scenario != required[sid]:
            fail(f"record scenario does not equal compiled obligation: {sid}")
        result = record.get("result") or {}
        evidence_key = record.get("evidence_key")
        if not evidence_key:
            fail(f"record missing evidence_key: {sid}")
        by_id[sid] = record
        mapping.append(
            {
                "requirement": f"REQ::{sid}",
                "failure_mode": f"FM::{scenario['rule']}",
                "rule": scenario["rule"],
                "scenario_id": sid,
                "required_proof_level": scenario.get("required_proof_level", "observed"),
                "evidence_type": result.get("proof_level", "observed"),
                "evidence_key": evidence_key,
                "status": result.get("status", "UNKNOWN"),
            }
        )

    missing = sorted(set(required) - set(by_id))
    if missing:
        fail(f"missing evidence records: {missing[:5]}")

    mapping.sort(key=lambda item: item["scenario_id"])
    passed = all(item["status"] == "PASS" for item in mapping)
    binding = current.get("binding") or {}
    required_binding = {
        "commit_sha",
        "scenario_digest",
        "rules_digest",
        "checker_digest",
        "environment_manifest_digest",
        "evidence_root",
    }
    if not required_binding.issubset(binding):
        fail("current_run_evidence binding is incomplete")

    report = {
        "checker": "traceability-current-run-v3-record-bound",
        "mapping": mapping,
        "required_obligations": len(scenarios),
        "traced_obligations": len(mapping),
        "percentage": 100 if len(mapping) == len(scenarios) else 0,
        "status": "PASS" if passed else "FAIL",
        **{key: binding[key] for key in required_binding},
        "generation_mode": "current-run",
        "source_run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    payload = {k: v for k, v in report.items() if k not in ("report_hash", "report_hash_algo")}
    report["report_hash"] = sha16_json(payload)
    report["report_hash_algo"] = "sha256:16"
    (REPORT_DIR / "traceability_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))

    print(
        "TRACEABILITY REPORT BUILT",
        json.dumps(
            {
                "required": len(scenarios),
                "mapped": len(mapping),
                "unique": len(by_id),
                "status": report["status"],
                "hash": report["report_hash"],
            },
            sort_keys=True,
        ),
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
