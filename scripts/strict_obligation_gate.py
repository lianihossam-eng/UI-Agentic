"""Independent fail-closed gate for compiled obligations and traceability.

Validates the freshly compiled Required Scenario Set against current-run records,
recomputes every Evidence DAG key/root from exact code+kernel+environment, checks
the record-bound traceability report, and derives proof/certificate validity.
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
from core.coverage import EvidenceDAG
from core.measurement_kernel import measurement_kernel_digest
from core.scenario_compiler import compile as compile_scenarios

REPORT_DIR = BASE / "reports"
PROOF_RANK = {"observed": 1, "bounded": 2, "certified": 3}
ROUTE_FILES = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}


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


def file_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def verify_report_hash(report: dict) -> None:
    expected = report.get("report_hash")
    if not expected:
        fail("traceability_report missing report_hash")
    payload = {k: v for k, v in report.items() if k not in ("report_hash", "report_hash_algo")}
    if sha16_json(payload) != expected:
        fail("traceability_report hash mismatch")


def expected_state(scenario: dict) -> str:
    if scenario["rule"].startswith("transition:"):
        return (scenario.get("transition") or {}).get("from", "default")
    return scenario.get("state", "default")


def validate_rendered_environment(scenario: dict, rendered: dict, domain: dict) -> None:
    sid = scenario["scenario_id"]
    if not isinstance(rendered, dict):
        fail(f"missing rendered environment: {sid}")
    if rendered.get("viewport_width") != scenario.get("viewport", 768):
        fail(f"rendered viewport width mismatch: {sid}")
    if rendered.get("viewport_height") != domain.get("viewport_height", 900):
        fail(f"rendered viewport height mismatch: {sid}")
    if float(rendered.get("device_pixel_ratio", -1)) != 1.0:
        fail(f"rendered DPR outside declared domain: {sid}")
    if rendered.get("document_direction") != "ltr":
        fail(f"rendered direction outside declared fr-LTR domain: {sid}")
    language = str(rendered.get("document_language") or "").lower()
    if not language.startswith("fr"):
        fail(f"rendered language outside declared fr-LTR domain: {sid}")
    if rendered.get("declared_locale_direction") != list(domain.get("locales_directions", [])):
        fail(f"declared locale/direction binding mismatch: {sid}")
    if rendered.get("declared_zoom_dpr") != list(domain.get("zoom_dpr", [])):
        fail(f"declared zoom/DPR binding mismatch: {sid}")
    if rendered.get("declared_inputs") != list(domain.get("input_modalities", [])):
        fail(f"declared input binding mismatch: {sid}")
    if rendered.get("state") != expected_state(scenario):
        fail(f"rendered state mismatch: {sid}")


def main() -> int:
    domain = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
    scenarios = compile_scenarios(domain)
    required = {scenario["scenario_id"]: scenario for scenario in scenarios}
    if len(required) != len(scenarios):
        fail("compiled scenario ids are not unique")

    current = load(REPORT_DIR / "current_run_evidence.json")
    browser = current.get("browser")
    if not isinstance(browser, str) or not browser.startswith("chromium@"):
        fail("current-run browser binding missing or invalid")
    records = current.get("records")
    if not isinstance(records, list) or len(records) != len(required):
        fail("current-run evidence record count mismatch")

    actual_measurement_digest = measurement_kernel_digest()
    records_by_id = {}
    reconstructed_dag = EvidenceDAG()

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

        readiness = record.get("readiness")
        if not isinstance(readiness, dict) or readiness.get("status") != "PASS":
            fail(f"full readiness evidence missing/not PASS: {sid}")
        if record.get("readiness_status") != "PASS":
            fail(f"readiness summary mismatch: {sid}")

        rendered = record.get("rendered_environment")
        validate_rendered_environment(scenario, rendered, domain)

        if record.get("measurement_kernel_digest") != actual_measurement_digest:
            fail(f"measurement kernel digest mismatch: {sid}")

        route = scenario.get("route")
        if route not in ROUTE_FILES:
            fail(f"unknown route file binding: {sid}")
        code_digest = file_hash(ROUTE_FILES[route])
        environment = {
            **rendered,
            "browser": browser,
            "measurement_kernel_digest": actual_measurement_digest,
            "readiness": readiness.get("checks", {}),
        }
        recomputed_key = reconstructed_dag.key(
            code_digest,
            "contract-public-audit-v1",
            scenario["rule"],
            scenario,
            browser,
            actual_measurement_digest,
            environment,
        )
        if record.get("evidence_key") != recomputed_key:
            fail(f"evidence key is not independently reproducible: {sid}")

        reconstructed_dag.put(
            recomputed_key,
            {
                "scenario": scenario,
                "result": result,
                "readiness": readiness,
                "rendered_environment": rendered,
                "measurement_kernel_digest": actual_measurement_digest,
            },
        )
        records_by_id[sid] = record

    if set(records_by_id) != set(required):
        fail("current-run evidence does not cover the exact required scenario set")

    reconstructed_root = reconstructed_dag.root_digest()
    if current.get("evidence_root") != reconstructed_root:
        fail(
            "Evidence DAG root mismatch: "
            f"artifact={current.get('evidence_root')} reconstructed={reconstructed_root}"
        )

    trace = load(REPORT_DIR / "traceability_report.json")
    verify_report_hash(trace)
    mapping = trace.get("mapping")
    if not isinstance(mapping, list) or len(mapping) != len(required):
        fail("traceability mapping count mismatch")
    if trace.get("required_obligations") != len(required) or trace.get("traced_obligations") != len(required):
        fail("traceability aggregate counts mismatch")
    if trace.get("percentage") != 100 or trace.get("status") != "PASS":
        fail("traceability report is not 100% PASS")
    if trace.get("evidence_root") != reconstructed_root:
        fail("traceability report is not bound to reconstructed Evidence DAG root")

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
                "measurement_kernel_digest": actual_measurement_digest,
                "reconstructed_evidence_root": reconstructed_root,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
