"""Independent fail-closed verifier for the complete mutation contract."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from scripts.fault_injection import MUTANTS

REPORT_DIR = BASE / "reports"


def fail(message: str) -> None:
    print(f"STRICT MUTATION FAIL: {message}", file=sys.stderr)
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
    report = load(REPORT_DIR / "mutation_report.json")
    expected_hash = report.get("report_hash")
    payload = {key: value for key, value in report.items() if key not in ("report_hash", "report_hash_algo")}
    if not expected_hash or sha16_json(payload) != expected_hash:
        fail("mutation report hash mismatch")
    if report.get("generation_mode") != "current-run" or report.get("status") != "PASS":
        fail("mutation report is not current-run PASS")

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
            fail(f"mutation binding mismatch: {field}")
    if report.get("browser") != current.get("browser"):
        fail("mutation browser mismatch")

    contract = {item["id"]: item for item in MUTANTS}
    details = report.get("details")
    if not isinstance(details, list):
        fail("mutation details missing")
    if report.get("mutants_total") != len(contract) or len(details) != len(contract):
        fail(f"mutation count mismatch: expected {len(contract)}")
    if report.get("survived") != 0 or report.get("critical_mutants_zero") is not True:
        fail("one or more mutants survived")

    seen = set()
    for detail in details:
        mutant_id = detail.get("id")
        if mutant_id not in contract:
            fail(f"unknown mutant result: {mutant_id}")
        if mutant_id in seen:
            fail(f"duplicate mutant result: {mutant_id}")
        seen.add(mutant_id)
        spec = contract[mutant_id]
        if detail.get("rule_expected") != spec["rule"]:
            fail(f"mutant rule mismatch: {mutant_id}")
        if detail.get("owner_expected") != spec["owner"]:
            fail(f"mutant owner mismatch: {mutant_id}")
        if detail.get("route") != spec["route"] or detail.get("viewport") != spec["viewport"]:
            fail(f"mutant scenario mismatch: {mutant_id}")
        if detail.get("baseline_status") != "PASS":
            fail(f"mutant baseline is not PASS: {mutant_id}")
        if detail.get("mutated_status") not in ("FAIL", "UNKNOWN"):
            fail(f"mutant was not detected as FAIL/UNKNOWN: {mutant_id}")
        if detail.get("detected") is not True:
            fail(f"mutant detection flag false: {mutant_id}")
        if detail.get("revert_status") != "PASS" or detail.get("revert_ok") is not True:
            fail(f"mutant revert is not PASS: {mutant_id}")
        if detail.get("survivor") is not False:
            fail(f"mutant survived: {mutant_id}")

    if seen != set(contract):
        fail("mutation results do not equal the exact mutation contract")

    print(
        "STRICT MUTATION PASS",
        json.dumps(
            {
                "mutants": len(contract),
                "killed": len(seen),
                "survived": 0,
                "ids": sorted(seen),
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
