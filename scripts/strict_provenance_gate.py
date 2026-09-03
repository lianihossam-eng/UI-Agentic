"""Strict current-run provenance gate.

Rejects metadata rebinding: automated reports must be generated in the current
job, the runtime manifest must match the process actually executing this
checker, current screenshots must match their manifest, and the final
attestation must bind the same commit/environment/evidence/report/visual roots.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import pathlib
import platform
import subprocess
import sys

import yaml
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.measurement_kernel import measurement_kernel_digest
from core.scenario_compiler import (
    compile as compile_scenarios,
    rule_contract_seed,
)

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


def fail(message: str) -> None:
    print(f"STRICT PROVENANCE FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def sha16_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def sha256_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def current_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE).decode().strip()
    except Exception as exc:
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
        key: value
        for key, value in data.items()
        if key not in ("report_hash", "report_hash_algo")
    }
    computed = sha16_json(payload)
    if computed != expected:
        fail(f"{name}: report_hash mismatch {computed} != {expected}")


def actual_browser_version() -> str:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        version = browser.version
        browser.close()
    return version


def verify_screenshots(visual: dict) -> None:
    expected = visual.get("screenshot_digests")
    if not isinstance(expected, dict) or not expected:
        fail("visual_review: screenshot_digests missing")
    current = {}
    for name in sorted(expected):
        path = BASE / "reports" / "screenshots" / name
        if not path.exists():
            fail(f"visual_review: missing screenshot {name}")
        current[name] = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    if current != expected:
        fail("visual_review: screenshot bytes do not match current-run digests")
    snapshot = sha16_json(current)
    if visual.get("snapshot_digest") != snapshot:
        fail("visual_review: snapshot digest mismatch")
    digests_file = load_json(BASE / "reports" / "screenshots" / "digests.json")
    if digests_file != current:
        fail("screenshots/digests.json does not match screenshot bytes")


def main() -> int:
    commit = current_commit()
    current_run_id = os.environ.get("GITHUB_RUN_ID", "local")

    domain = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
    scenarios = compile_scenarios(domain)
    scenario_digest = sha16_json(scenarios)
    rules_digest = hashlib.sha256(
        (BASE / "supported-domain.yaml").read_bytes()
        + json.dumps(rule_contract_seed(), sort_keys=True).encode()
    ).hexdigest()[:16]
    measurement_digest = measurement_kernel_digest()
    checker_digest = measurement_digest[:16]

    manifest = load_json(BASE / "reports" / "environment_manifest.json")
    manifest_payload = {
        key: value
        for key, value in manifest.items()
        if key not in ("manifest_digest", "manifest_hash_algo")
    }
    manifest_digest = sha16_json(manifest_payload)
    if manifest.get("manifest_digest") != manifest_digest:
        fail("environment_manifest.json digest mismatch")
    if manifest.get("generation_mode") != "current-run":
        fail("environment manifest was not generated from current run")
    if manifest.get("commit_sha") != commit or manifest.get("github_sha") != commit:
        fail("environment manifest commit/github_sha mismatch")
    if str(manifest.get("github_run_id")) != str(current_run_id):
        fail("environment manifest run id mismatch")
    if manifest.get("scenario_digest") != scenario_digest:
        fail("environment manifest scenario digest mismatch")
    if manifest.get("rules_digest") != rules_digest:
        fail("environment manifest rules digest mismatch")
    if manifest.get("checker_digest") != checker_digest:
        fail("environment manifest checker digest mismatch")
    if manifest.get("measurement_kernel_digest") != measurement_digest:
        fail("environment manifest measurement kernel mismatch")
    if manifest.get("python_version") != platform.python_version():
        fail(
            f"environment python mismatch {manifest.get('python_version')} != {platform.python_version()}"
        )
    installed_playwright = importlib.metadata.version("playwright")
    if manifest.get("playwright_version") != installed_playwright:
        fail(
            "environment Playwright mismatch "
            f"{manifest.get('playwright_version')} != {installed_playwright}"
        )
    browser_version = actual_browser_version()
    if manifest.get("chromium_version") != browser_version:
        fail(
            f"environment Chromium mismatch {manifest.get('chromium_version')} != {browser_version}"
        )
    runner_os = os.environ.get("RUNNER_OS")
    if runner_os and manifest.get("runner_os") != runner_os:
        fail("environment runner_os mismatch")

    current_run = load_json(BASE / "reports" / "current_run_evidence.json")
    if current_run.get("generation_mode") != "current-run":
        fail("current_run_evidence is not current-run generated")
    if str(current_run.get("source_run_id")) != str(current_run_id):
        fail("current_run_evidence run id mismatch")
    binding = current_run.get("binding") or {}
    if binding.get("commit_sha") != commit:
        fail("current_run_evidence commit mismatch")
    if current_run.get("environment_manifest_digest") != manifest_digest:
        fail("current_run_evidence manifest mismatch")
    if current_run.get("evidence_root") != manifest.get("evidence_root"):
        fail("current_run_evidence root mismatch")
    if current_run.get("measurement_kernel_digest") != measurement_digest:
        fail("current_run_evidence measurement kernel mismatch")
    if (current_run.get("reproducibility") or {}).get("passed") is not True:
        fail("current_run_evidence A/B reproducibility not proved")

    records = current_run.get("records")
    if not isinstance(records, list) or not records:
        fail("current_run_evidence records missing")
    for record in records:
        if record.get("measurement_kernel_digest") != measurement_digest:
            fail("evidence record measurement kernel mismatch")

    expected_binding = {
        "commit_sha": commit,
        "scenario_digest": scenario_digest,
        "rules_digest": rules_digest,
        "checker_digest": checker_digest,
        "environment_manifest_digest": manifest_digest,
        "evidence_root": current_run.get("evidence_root"),
    }

    report_hashes = {}
    reports = {}
    for name in REPORT_NAMES:
        data = load_json(BASE / "reports" / f"{name}.json")
        reports[name] = data
        verify_report_hash(name, data)
        if data.get("generation_mode") != "current-run":
            fail(f"{name}: report is not semantic current-run output")
        if str(data.get("source_run_id")) != str(current_run_id):
            fail(f"{name}: source_run_id mismatch")
        for field in REQUIRED_BINDING_FIELDS:
            if field not in data:
                fail(f"{name}: missing mandatory binding field {field}")
            if data.get(field) != expected_binding[field]:
                fail(
                    f"{name}: binding mismatch {field}: "
                    f"{data.get(field)} != {expected_binding[field]}"
                )
        report_hashes[name] = data["report_hash"]

    visual = reports["visual_review"]
    verify_screenshots(visual)
    if visual.get("verdict") != "ACCEPTED" or visual.get("status") != "PASS":
        fail("visual review is not ACCEPTED")
    if not visual.get("reviewer") or not visual.get("reviewed_at"):
        fail("visual review lacks reviewer/reviewed_at")
    if current_run.get("visual_snapshot_digest") != visual.get("snapshot_digest"):
        fail("current_run_evidence visual root mismatch")

    final_result = load_json(BASE / "reports" / "final_result.json")
    gate = final_result.get("final_gate") or {}
    if gate.get("passed") is not True or gate.get("blocking_gates"):
        fail("final_result Final Gate is not closed")
    if final_result.get("evidence_root") != current_run.get("evidence_root"):
        fail("final_result evidence root mismatch")
    if final_result.get("measurement_kernel_digest") != measurement_digest:
        fail("final_result measurement kernel mismatch")
    if final_result.get("browser") != manifest.get("browser"):
        fail("final_result browser mismatch")

    attestation = load_json(BASE / ".goal_attestation.json")
    if attestation.get("verdict") != "LOCKED":
        fail(".goal_attestation.json is not LOCKED")
    payload = attestation.get("attestation") or {}
    digest = sha256_json(payload)
    if attestation.get("digest_algo") != "sha256" or attestation.get("digest") != digest:
        fail("attestation digest invalid")
    reports_root = sha256_json(report_hashes)
    subject = payload.get("subject") or {}
    required_attestation = {
        "commit_sha": subject.get("commit_sha"),
        "scenario_digest": payload.get("scenario_digest"),
        "rules_digest": payload.get("rules_digest"),
        "checker_digest": payload.get("checker_digest"),
        "environment_manifest_digest": payload.get("environment_manifest_digest"),
        "evidence_root": payload.get("evidence_root"),
        "reports_root": payload.get("reports_root"),
        "visual_evidence_root": payload.get("visual_evidence_root"),
        "source_run_id": str(payload.get("source_run_id")),
    }
    expected_attestation = {
        "commit_sha": commit,
        "scenario_digest": scenario_digest,
        "rules_digest": rules_digest,
        "checker_digest": checker_digest,
        "environment_manifest_digest": manifest_digest,
        "evidence_root": current_run.get("evidence_root"),
        "reports_root": reports_root,
        "visual_evidence_root": visual.get("snapshot_digest"),
        "source_run_id": str(current_run_id),
    }
    if required_attestation != expected_attestation:
        fail(
            "attestation binding mismatch: "
            + json.dumps(
                {
                    "actual": required_attestation,
                    "expected": expected_attestation,
                },
                sort_keys=True,
            )
        )
    if (payload.get("final_gate") or {}).get("passed") is not True:
        fail("attestation final gate is not PASS")

    print(
        "STRICT CURRENT-RUN PROVENANCE PASS",
        json.dumps(
            {
                "commit_sha": commit,
                "run_id": current_run_id,
                "browser": manifest.get("browser"),
                "python": manifest.get("python_version"),
                "playwright": manifest.get("playwright_version"),
                "measurement_kernel_digest": measurement_digest,
                "environment_manifest_digest": manifest_digest,
                "evidence_root": current_run.get("evidence_root"),
                "reports_root": reports_root,
                "visual_evidence_root": visual.get("snapshot_digest"),
                "attestation_digest": attestation.get("digest"),
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
