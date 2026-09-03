"""Generate semantic proof artifacts from the exact current CI/browser run.

Browser measurement is delegated exclusively to core.replay_engine. This script
runs the compiled Supported Domain twice (A/B), requires identical coverage and
Evidence DAG roots, then derives current-run reports from those exact records.
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
from datetime import datetime, timezone

import yaml

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.replay_engine import replay
from core.scenario_compiler import compile as compile_scenarios

DOMAIN = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
SCENARIOS = compile_scenarios(DOMAIN)
ROUTE_FILE = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}
REPORT_DIR = BASE / "reports"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
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
OWNER_BY_RULE = {
    "group.uniform_gap": "SECTION",
    "global.spacing.scale": "GLOBAL",
    "breakpoint.shell.direction": "FAMILY",
    "paint.contrast.text": "PAGE",
    "component.button.hit-target": "COMPONENT",
    "TARGET_OPERABLE": "COMPONENT",
    "accessibility.focus-order": "PAGE",
    "FOCUS_USABLE": "COMPONENT",
    "temporal.geometry-stable": "PAGE",
    "MODAL_INTEGRITY": "PAGE",
}
BINDING_FIELDS = (
    "commit_sha",
    "scenario_digest",
    "rules_digest",
    "checker_digest",
    "environment_manifest_digest",
    "evidence_root",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha16_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE).decode().strip()


def os_pretty_name() -> str:
    path = pathlib.Path("/etc/os-release")
    if not path.exists():
        return platform.system()
    values = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values.get("PRETTY_NAME", platform.system())


def add_report_hash(payload: dict) -> dict:
    data = {key: value for key, value in payload.items() if key not in ("report_hash", "report_hash_algo")}
    payload["report_hash"] = sha16_json(data)
    payload["report_hash_algo"] = "sha256:16"
    return payload


def write_report(name: str, payload: dict, binding: dict, run_id: str, generated_at: str) -> dict:
    data = dict(payload)
    data.update(binding)
    data["generation_mode"] = "current-run"
    data["source_run_id"] = run_id
    data["generated_at"] = generated_at
    add_report_hash(data)
    (REPORT_DIR / f"{name}.json").write_text(json.dumps(data, indent=2, sort_keys=True))
    return data


def screenshot_digests() -> dict[str, str]:
    expected = {
        f"{route.strip('/')}-{viewport}.png"
        for route in DOMAIN["routes"]
        for viewport in DOMAIN["viewport_widths"]
    }
    actual = {path.name for path in SCREENSHOT_DIR.glob("*.png")}
    if actual != expected:
        raise RuntimeError(
            f"default screenshot matrix mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}"
        )
    return {
        name: hashlib.sha256((SCREENSHOT_DIR / name).read_bytes()).hexdigest()[:16]
        for name in sorted(expected)
    }


def exact_replay_match(first: dict, second: dict) -> bool:
    if first["coverage"] != second["coverage"] or first["evidence_root"] != second["evidence_root"]:
        return False
    first_pairs = [
        (record["scenario"].get("scenario_id"), record["result"].get("status"), record.get("evidence_key"))
        for record in first["records"]
    ]
    second_pairs = [
        (record["scenario"].get("scenario_id"), record["result"].get("status"), record.get("evidence_key"))
        for record in second["records"]
    ]
    return first_pairs == second_pairs


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    run_id = str(os.environ.get("GITHUB_RUN_ID", "local"))
    commit = current_commit()

    first = replay(
        domain=DOMAIN,
        scenarios=SCENARIOS,
        route_files=ROUTE_FILE,
        capture_screenshots=True,
        screenshot_dir=SCREENSHOT_DIR,
    )
    second = replay(
        domain=DOMAIN,
        scenarios=SCENARIOS,
        route_files=ROUTE_FILE,
        capture_screenshots=False,
    )

    if not first["coverage"].get("closed") or not exact_replay_match(first, second):
        print("CURRENT-RUN EVIDENCE FAIL: A/B replay mismatch or coverage not closed", file=sys.stderr)
        print(
            json.dumps(
                {
                    "A": first["coverage"],
                    "B": second["coverage"],
                    "rootA": first["evidence_root"],
                    "rootB": second["evidence_root"],
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    scenario_digest = sha16_json(SCENARIOS)
    rules_digest = hashlib.sha256(
        (BASE / "supported-domain.yaml").read_bytes()
        + json.dumps(RULES_SEED, sort_keys=True).encode()
    ).hexdigest()[:16]
    checker_digest = hashlib.sha256(
        b"".join((BASE / path).read_bytes() for path in CHECKER_FILES)
    ).hexdigest()[:16]

    browser_raw = first["browser"].split("@", 1)[1]
    manifest = {
        "commit_sha": commit,
        "github_sha": os.environ.get("GITHUB_SHA", commit),
        "github_run_id": run_id,
        "runner_os": os.environ.get("RUNNER_OS", platform.system()),
        "runner_arch": os.environ.get("RUNNER_ARCH", platform.machine()),
        "image_os": os.environ.get("ImageOS"),
        "image_version": os.environ.get("ImageVersion"),
        "os": os_pretty_name(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "playwright_version": importlib.metadata.version("playwright"),
        "chromium_version": browser_raw,
        "browser": first["browser"],
        "locale": DOMAIN.get("locales_directions", ["fr-LTR"])[0],
        "dpr": "1",
        "viewport_height": DOMAIN.get("viewport_height", 900),
        "viewport_widths": DOMAIN.get("viewport_widths", []),
        "scenario_digest": scenario_digest,
        "rules_digest": rules_digest,
        "checker_digest": checker_digest,
        "evidence_root": first["evidence_root"],
        "captured_at": generated_at,
        "generation_mode": "current-run",
    }
    manifest_payload = {
        key: value for key, value in manifest.items()
        if key not in ("manifest_digest", "manifest_hash_algo")
    }
    manifest["manifest_digest"] = sha16_json(manifest_payload)
    manifest["manifest_hash_algo"] = "sha256:16"
    (REPORT_DIR / "environment_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))

    binding = {
        "commit_sha": commit,
        "scenario_digest": scenario_digest,
        "rules_digest": rules_digest,
        "checker_digest": checker_digest,
        "environment_manifest_digest": manifest["manifest_digest"],
        "evidence_root": first["evidence_root"],
    }

    assumptions = [
        {"id": "A1", "category": "fixture", "text": "verification targets repository file:// demo fixtures only"},
        {"id": "A2", "category": "browser", "text": f"supported browser is {first['browser']} for this attested run"},
        {"id": "A3", "category": "locale", "text": f"locale/direction scope is {DOMAIN.get('locales_directions', [])}"},
        {"id": "A4", "category": "display", "text": f"DPR/zoom scope is {DOMAIN.get('zoom_dpr', [])}"},
        {"id": "A5", "category": "network", "text": "demo fixtures require no remote application network dependency"},
        {"id": "A6", "category": "temporal", "text": f"temporal scope is {DOMAIN.get('temporal_scenarios', [])}"},
        {"id": "A7", "category": "compliance", "text": f"compliance profiles are {DOMAIN.get('compliance_profiles', [])}"},
        {"id": "A8", "category": "visual", "text": "visual acceptance is external and reusable only by exact screenshot snapshot digest"},
    ]
    required_categories = {"fixture", "browser", "locale", "display", "network", "temporal", "compliance", "visual"}
    documented_categories = {item["category"] for item in assumptions}
    assumptions_complete = documented_categories == required_categories
    write_report(
        "assumptions_report",
        {
            "assumptions": [],
            "documented_assumptions": assumptions,
            "required_categories": sorted(required_categories),
            "documented_categories": sorted(documented_categories),
            "unstated_count": 0 if assumptions_complete else len(required_categories - documented_categories),
            "status": "PASS" if assumptions_complete else "FAIL",
        },
        binding,
        run_id,
        generated_at,
    )

    grouped = {}
    for record in first["records"]:
        scenario = record["scenario"]
        result = record["result"]
        rule = scenario["rule"]
        owner = result.get("owner") or OWNER_BY_RULE.get(rule, "PAGE" if rule.startswith("transition:") else "UNKNOWN")
        key = f"{owner}:{rule}"
        entry = grouped.setdefault(
            key,
            {"owner": owner, "rule": rule, "required": 0, "passed": 0, "failed": 0, "unknown": 0},
        )
        entry["required"] += 1
        status = result.get("status", "UNKNOWN")
        if status == "PASS":
            entry["passed"] += 1
        elif status == "FAIL":
            entry["failed"] += 1
        else:
            entry["unknown"] += 1
    parent_checks = []
    for entry in grouped.values():
        entry["valid"] = entry["required"] == entry["passed"] and entry["failed"] == 0 and entry["unknown"] == 0
        parent_checks.append(entry)
    parent_valid = bool(parent_checks) and all(item["valid"] for item in parent_checks)
    write_report(
        "parent_contract_report",
        {
            "contracts": sorted(parent_checks, key=lambda item: (item["owner"], item["rule"])),
            "all_valid": parent_valid,
            "status": "PASS" if parent_valid else "FAIL",
        },
        binding,
        run_id,
        generated_at,
    )

    cross_rules = ("TARGET_OPERABLE", "FOCUS_USABLE", "MODAL_INTEGRITY")
    bundles = {}
    snapshot = {}
    for rule in cross_rules:
        matches = [record for record in first["records"] if record["scenario"]["rule"] == rule]
        passed = bool(matches) and all(record["result"].get("status") == "PASS" for record in matches)
        bundles[rule] = {
            "required": len(matches),
            "passed": sum(record["result"].get("status") == "PASS" for record in matches),
            "evidence_keys": [record["evidence_key"] for record in matches],
            "statuses": [record["result"].get("status", "UNKNOWN") for record in matches],
            "verified": passed,
        }
        snapshot[f"{rule}_status"] = "PASS" if passed else "FAIL"
    snapshot["all_pass"] = all(bundle["verified"] for bundle in bundles.values())
    write_report(
        "cross_layer_report",
        {
            "evidence_bundles": bundles,
            "snapshot_evidence": snapshot,
            "complete": snapshot["all_pass"],
            "status": "PASS" if snapshot["all_pass"] else "FAIL",
        },
        binding,
        run_id,
        generated_at,
    )

    regression_closed = exact_replay_match(first, second)
    write_report(
        "regression_report",
        {
            "run_a_evidence_root": first["evidence_root"],
            "run_b_evidence_root": second["evidence_root"],
            "run_a_coverage": first["coverage"],
            "run_b_coverage": second["coverage"],
            "closed": regression_closed,
            "status": "PASS" if regression_closed else "FAIL",
        },
        binding,
        run_id,
        generated_at,
    )

    mutation_path = REPORT_DIR / "mutation_report.json"
    if not mutation_path.exists():
        raise RuntimeError("mutation_report.json missing: run fault_injection.py first")
    mutation = json.loads(mutation_path.read_text())
    details = mutation.get("details", [])
    mutation_semantic_ok = (
        bool(details)
        and mutation.get("survived") == 0
        and all(
            item.get("baseline_status") == "PASS"
            and item.get("detected") is True
            and item.get("mutated_status") in ("FAIL", "UNKNOWN")
            and item.get("revert_status") == "PASS"
            and item.get("survivor") is False
            for item in details
        )
        and mutation.get("browser") == first["browser"]
    )
    mutation_payload = {
        key: value
        for key, value in mutation.items()
        if key not in set(BINDING_FIELDS)
        | {"report_hash", "report_hash_algo", "generated_at", "generation_mode", "source_run_id"}
    }
    mutation_payload["status"] = "PASS" if mutation_semantic_ok else "FAIL"
    mutation_payload["critical_mutants_zero"] = mutation_semantic_ok
    write_report("mutation_report", mutation_payload, binding, run_id, generated_at)

    default_digests = screenshot_digests()
    (SCREENSHOT_DIR / "digests.json").write_text(json.dumps(default_digests, indent=2, sort_keys=True))
    default_snapshot = sha16_json(default_digests)
    write_report(
        "visual_review",
        {
            "contract": "visual-v3-exact-snapshot",
            "verdict": "UNKNOWN",
            "status": "UNKNOWN",
            "reason": "complete-25-image-visual-contract-not-yet-enforced",
            "reviewer": None,
            "reviewer_type": None,
            "reviewed_at": None,
            "rubric": None,
            "approval_source": "reports/visual_approval.json",
            "reference_images": "reports/screenshots/current-run",
            "screenshots_manifest": "reports/screenshots/digests.json",
            "screenshot_count": len(default_digests),
            "screenshot_digests": default_digests,
            "snapshot_digest": default_snapshot,
            "source": "default-state screenshots regenerated by exact current CI/browser run",
        },
        binding,
        run_id,
        generated_at,
    )

    current_run = {
        "generation_mode": "current-run",
        "source_run_id": run_id,
        "generated_at": generated_at,
        "binding": binding,
        "environment_manifest_digest": manifest["manifest_digest"],
        "browser": first["browser"],
        "coverage": first["coverage"],
        "evidence_root": first["evidence_root"],
        "reproducibility": {
            "passed": regression_closed,
            "run_a_root": first["evidence_root"],
            "run_b_root": second["evidence_root"],
        },
        "visual_snapshot_digest": default_snapshot,
        "visual_accepted": False,
        "records": first["records"],
    }
    current_run["artifact_hash"] = sha16_json(current_run)
    (REPORT_DIR / "current_run_evidence.json").write_text(json.dumps(current_run, indent=2, sort_keys=True))

    print(
        "CURRENT-RUN EVIDENCE GENERATED",
        json.dumps(
            {
                "commit": commit,
                "run_id": run_id,
                "browser": first["browser"],
                "python": platform.python_version(),
                "playwright": importlib.metadata.version("playwright"),
                "coverage": first["coverage"],
                "evidence_root": first["evidence_root"],
                "manifest_digest": manifest["manifest_digest"],
                "visual_snapshot": default_snapshot,
                "visual_accepted": False,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
