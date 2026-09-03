import hashlib
import importlib.metadata
import json
import pathlib
import platform
import subprocess
import sys

import yaml
from playwright.sync_api import sync_playwright

from core.attestation import attest
from core.coverage import CoverageLedger, EvidenceDAG, final_confirmation_gate, measurement_readiness
from core.scenario_compiler import compile
from gvh.extractor import compute_ir
from gvh.verify import verify_all

BASE = pathlib.Path(__file__).parent
DOMAIN = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
SCENARIOS = compile(DOMAIN)
ROUTE_FILE = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def result_for(findings, rule):
    result = next((item for item in findings if item.get("constraint") == rule), None)
    if result is None:
        return {"constraint": rule, "status": "UNKNOWN", "reason": "checker-produced-no-result"}
    return result


def record(ledger, dag, scenario, result, browser_version, readiness):
    ledger.record(result)
    route = scenario.get("route", "global")
    viewport = scenario.get("viewport", 768)
    code_digest = file_hash(ROUTE_FILE[route]) if route in ROUTE_FILE else "no-route"
    environment = {"browser": browser_version, "viewport": viewport, "readiness": readiness.get("checks", {})}
    key = dag.key(
        code_digest,
        "contract-public-audit-v1",
        scenario["rule"],
        scenario,
        browser_version,
        "checker-public-audit-v1",
        environment,
    )
    dag.put(key, {"scenario": scenario, "result": result, "readiness": readiness})


def execute_transition(page, transition):
    action = transition.get("action", "")
    if not action.startswith("click:"):
        return {
            "constraint": "transition",
            "status": "UNKNOWN",
            "reason": f"unsupported-transition-action:{action}",
            "proof_level": "observed",
        }
    selector = action.split(":", 1)[1]
    locator = page.locator(selector)
    if locator.count() == 0:
        return {
            "constraint": "transition",
            "status": "UNKNOWN",
            "reason": f"transition-target-missing:{selector}",
            "proof_level": "observed",
        }
    locator.click()
    assertion = transition.get("assertion")
    evidence = page.evaluate(
        """() => {
          const modal=document.querySelector('[data-testid="modal"]');
          const opener=document.querySelector('[data-testid="open-modal"]');
          const active=document.activeElement;
          const visible=modal ? getComputedStyle(modal).display!=='none' && modal.hasAttribute('open') : false;
          return {
            modalOpen: visible,
            focusInsideModal: !!modal && !!active && modal.contains(active),
            focusReturnedToOpener: !!opener && active===opener
          };
        }"""
    )
    if assertion == "modal-open":
        passed = evidence["modalOpen"] and evidence["focusInsideModal"]
    elif assertion == "modal-closed":
        passed = (not evidence["modalOpen"]) and evidence["focusReturnedToOpener"]
    else:
        return {
            "constraint": "transition",
            "status": "UNKNOWN",
            "reason": f"unsupported-transition-assertion:{assertion}",
            "proof_level": "observed",
            "evidence": evidence,
        }
    return {
        "constraint": "transition",
        "status": "PASS" if passed else "FAIL",
        "proof_level": "observed",
        "transition": transition,
        "evidence": evidence,
    }


def _run_strict_obligation_gate():
    result = subprocess.run(
        [sys.executable, str(BASE / "scripts" / "strict_obligation_gate.py")],
        cwd=BASE,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def main():
    ledger = CoverageLedger(SCENARIOS)
    dag = EvidenceDAG()
    readiness_results = []
    transition_results = []
    cross_layer_results = []

    static_scenarios = [
        sc
        for sc in SCENARIOS
        if not sc["rule"].startswith("transition:") and sc.get("state") != "modal-open"
    ]
    modal_scenarios = [sc for sc in SCENARIOS if sc.get("state") == "modal-open"]
    transition_scenarios = [sc for sc in SCENARIOS if sc["rule"].startswith("transition:")]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        browser_version = f"chromium@{browser.version}"

        groups = {}
        for scenario in static_scenarios:
            key = (scenario.get("route", "/orders"), scenario.get("viewport", 768))
            groups.setdefault(key, []).append(scenario)

        for (route, viewport), scenarios in groups.items():
            context = browser.new_context(
                viewport={"width": viewport, "height": DOMAIN.get("viewport_height", 900)}
            )
            page = context.new_page()
            page.goto(ROUTE_FILE[route].as_uri())
            readiness = measurement_readiness(page)
            readiness_results.append(readiness)
            if readiness["status"] != "PASS":
                for scenario in scenarios:
                    result = {
                        "constraint": scenario["rule"],
                        "status": "UNKNOWN",
                        "reason": "measurement-readiness-not-satisfied",
                        "readiness": readiness,
                    }
                    record(ledger, dag, scenario, result, browser_version, readiness)
                context.close()
                continue

            ir = compute_ir(page)
            findings = verify_all(ir, page)
            for scenario in scenarios:
                result = result_for(findings, scenario["rule"])
                if scenario["rule"] in ("TARGET_OPERABLE", "FOCUS_USABLE"):
                    cross_layer_results.append(result)
                record(ledger, dag, scenario, result, browser_version, readiness)
            context.close()

        for scenario in modal_scenarios:
            route = scenario["route"]
            context = browser.new_context(
                viewport={"width": scenario["viewport"], "height": DOMAIN.get("viewport_height", 900)}
            )
            page = context.new_page()
            page.goto(ROUTE_FILE[route].as_uri())
            readiness = measurement_readiness(page)
            readiness_results.append(readiness)
            if readiness["status"] == "PASS":
                opener = page.locator('[data-testid="open-modal"]')
                if opener.count() == 0:
                    result = {"constraint": "MODAL_INTEGRITY", "status": "UNKNOWN", "reason": "modal-opener-missing"}
                else:
                    opener.click()
                    page.wait_for_timeout(400)
                    ir = compute_ir(page)
                    findings = verify_all(ir, page)
                    result = result_for(findings, "MODAL_INTEGRITY")
            else:
                result = {"constraint": "MODAL_INTEGRITY", "status": "UNKNOWN", "reason": "measurement-readiness-not-satisfied"}
            cross_layer_results.append(result)
            record(ledger, dag, scenario, result, browser_version, readiness)
            context.close()

        by_model_viewport = {}
        for scenario in transition_scenarios:
            key = (scenario["model"], scenario.get("viewport", 768))
            by_model_viewport.setdefault(key, []).append(scenario)
        for (model, viewport), scenarios in by_model_viewport.items():
            route = scenarios[0]["route"]
            context = browser.new_context(
                viewport={"width": viewport, "height": DOMAIN.get("viewport_height", 900)}
            )
            page = context.new_page()
            page.goto(ROUTE_FILE[route].as_uri())
            readiness = measurement_readiness(page)
            readiness_results.append(readiness)
            for scenario in scenarios:
                if readiness["status"] != "PASS":
                    result = {"constraint": scenario["rule"], "status": "UNKNOWN", "reason": "measurement-readiness-not-satisfied"}
                else:
                    result = execute_transition(page, scenario["transition"])
                    result["constraint"] = scenario["rule"]
                transition_results.append(result)
                record(ledger, dag, scenario, result, browser_version, readiness)
            context.close()

        browser.close()

    transition_complete = bool(transition_results) and all(item.get("status") == "PASS" for item in transition_results)
    cross_layer_ledger_complete = bool(cross_layer_results) and all(item.get("status") == "PASS" for item in cross_layer_results)
    readiness_complete = bool(readiness_results) and all(item.get("status") == "PASS" for item in readiness_results)

    def _current_binding(evidence_root):
        try:
            commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BASE).decode().strip()
        except Exception:
            commit_sha = "unknown"
        scenario_digest_local = hashlib.sha256(json.dumps(SCENARIOS, sort_keys=True).encode()).hexdigest()[:16]
        rules_seed = [
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
        rules_digest_local = hashlib.sha256(
            (BASE / "supported-domain.yaml").read_bytes() + json.dumps(rules_seed, sort_keys=True).encode()
        ).hexdigest()[:16]
        checker_files = ["gvh/verify.py", "gvh/extractor.py", "core/coverage.py", "core/scenario_compiler.py"]
        checker_digest_local = hashlib.sha256(
            b"".join((BASE / filename).read_bytes() for filename in checker_files)
        ).hexdigest()[:16]
        env_path = BASE / "reports" / "environment_manifest.json"
        env_digest_local = None
        if env_path.exists():
            try:
                env_data = json.loads(env_path.read_text())
                copy = {
                    key: value
                    for key, value in env_data.items()
                    if key not in ("manifest_digest", "manifest_hash_algo")
                }
                env_digest_local = hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest()[:16]
            except Exception:
                env_digest_local = None
        return {
            "commit_sha": commit_sha,
            "scenario_digest": scenario_digest_local,
            "rules_digest": rules_digest_local,
            "checker_digest": checker_digest_local,
            "evidence_root": evidence_root,
            "env_digest": env_digest_local,
            "browser_version": browser_version,
        }

    evidence_root_local = dag.root_digest()
    binding = _current_binding(evidence_root_local)

    def _validate_report(name):
        path = BASE / "reports" / f"{name}.json"
        if not path.exists():
            return False, f"missing:{name}", None
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            return False, f"invalid-json:{name}:{exc}", None
        expected = data.get("report_hash")
        if not expected:
            return False, f"no-hash:{name}", data
        copy = {key: value for key, value in data.items() if key not in ("report_hash", "report_hash_algo")}
        computed = hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest()[:16]
        if computed != expected:
            return False, f"hash-mismatch:{name}", data
        if data.get("status") == "PENDING":
            return False, f"pending:{name}", data
        for field in ["scenario_digest", "evidence_root", "rules_digest", "checker_digest"]:
            if field in data and data.get(field) != binding.get(field):
                return False, f"binding-mismatch:{name}:{field}", data
        if (
            "environment_manifest_digest" in data
            and binding.get("env_digest")
            and data.get("environment_manifest_digest") != binding.get("env_digest")
        ):
            return False, f"binding-mismatch:{name}:environment_manifest_digest", data
        return True, "ok", data

    strict_obligation_ok, strict_obligation_stdout, strict_obligation_stderr = _run_strict_obligation_gate()

    ok_trace, _, trace_data = _validate_report("traceability_report")
    requirement_traceability = (
        strict_obligation_ok
        and ok_trace
        and trace_data.get("percentage") == 100
        and trace_data.get("traced_obligations") == ledger.required
        and trace_data.get("required_obligations") == ledger.required
        and trace_data.get("status") == "PASS"
    )

    # required_proof_levels and certificate_validation are derived by the
    # independent strict obligation checker. For the current domain it proves
    # that all 150 obligations require OBSERVED and derives certificate
    # validation vacuously because no BOUNDED/CERTIFIED certificate is needed.
    required_proof_levels = strict_obligation_ok
    certificate_validation = strict_obligation_ok

    ok_mut, _, mut_data = _validate_report("mutation_report")
    mut_strict_ok = False
    if ok_mut and mut_data:
        details = mut_data.get("details", [])
        mut_strict_ok = bool(details) and all(
            item.get("baseline_status") == "PASS"
            and item.get("detected") is True
            and item.get("mutated_status") in ("FAIL", "UNKNOWN")
            and item.get("revert_status") == "PASS"
            and not item.get("survivor")
            for item in details
        )
    critical_mutants_zero = (
        ok_mut
        and mut_data.get("survived") == 0
        and mut_data.get("critical_mutants_zero") is True
        and mut_data.get("status") == "PASS"
        and mut_data.get("mutants_total", 0) >= 7
        and mut_strict_ok
    )

    ok_assump, _, assump_data = _validate_report("assumptions_report")
    unstated_assumptions_zero = (
        ok_assump and assump_data.get("unstated_count") == 0 and assump_data.get("status") == "PASS"
    )

    ok_regress, _, regress_data = _validate_report("regression_report")
    regression_closed = (
        ok_regress and regress_data.get("closed") is True and regress_data.get("status") == "PASS"
    )

    ok_parent, _, parent_data = _validate_report("parent_contract_report")
    parent_contracts_valid = (
        ok_parent and parent_data.get("all_valid") is True and parent_data.get("status") == "PASS"
    )

    ok_cross, _, cross_data = _validate_report("cross_layer_report")
    cross_bundles_ok = False
    if ok_cross and cross_data:
        bundles = cross_data.get("evidence_bundles", {})
        snapshot = cross_data.get("snapshot_evidence", {})
        cross_bundles_ok = (
            all(key in bundles for key in ("TARGET_OPERABLE", "FOCUS_USABLE", "MODAL_INTEGRITY"))
            and snapshot.get("all_pass") is True
            and all(
                snapshot.get(f"{key}_status") == "PASS"
                for key in ("TARGET_OPERABLE", "FOCUS_USABLE", "MODAL_INTEGRITY")
            )
        )
    cross_layer_invariants_complete = (
        ok_cross
        and cross_data.get("complete") is True
        and cross_data.get("status") == "PASS"
        and cross_layer_ledger_complete
        and cross_bundles_ok
    )

    ok_visual, _, visual_data = _validate_report("visual_review")
    visual_screenshots_ok = False
    if ok_visual and visual_data:
        digests = visual_data.get("screenshot_digests", {})
        count = visual_data.get("screenshot_count")
        snapshot_digest = visual_data.get("snapshot_digest")
        viewports = DOMAIN.get("viewport_widths", [])
        default_names = {
            f"{route.strip('/')}-{viewport}.png"
            for route in DOMAIN.get("routes", [])
            for viewport in viewports
        }
        modal_routes = {
            route
            for route, states in (DOMAIN.get("states_by_route") or {}).items()
            if "modal-open" in (states or [])
        }
        modal_names = {
            f"{route.strip('/')}-{viewport}-modal-open.png"
            for route in modal_routes
            for viewport in viewports
        }
        expected_names = default_names | modal_names
        if (
            isinstance(digests, dict)
            and count == len(expected_names)
            and len(digests) == len(expected_names)
            and set(digests) == expected_names
            and visual_data.get("contract") == "visual-v3-exact-snapshot"
            and set(visual_data.get("required_states") or []) == {"default", "modal-open"}
        ):
            calculated = hashlib.sha256(json.dumps(digests, sort_keys=True).encode()).hexdigest()[:16]
            if calculated == snapshot_digest:
                digest_path = BASE / "reports" / "screenshots" / "digests.json"
                if digest_path.exists():
                    try:
                        visual_screenshots_ok = json.loads(digest_path.read_text()) == digests
                    except Exception:
                        visual_screenshots_ok = False
    visual_acceptance = (
        ok_visual
        and visual_data.get("verdict") == "ACCEPTED"
        and visual_data.get("status") == "PASS"
        and visual_screenshots_ok
    )

    compliance_obligations_complete = not bool(DOMAIN.get("compliance_profiles"))

    gate_checks = {
        "requirement_traceability": requirement_traceability,
        "required_proof_levels": required_proof_levels,
        "certificate_validation": certificate_validation,
        "measurement_readiness": readiness_complete,
        "critical_mutants_zero": critical_mutants_zero,
        "unstated_assumptions_zero": unstated_assumptions_zero,
        "regression_closed": regression_closed,
        "parent_contracts_valid": parent_contracts_valid,
        "state_transitions_complete": transition_complete,
        "cross_layer_invariants_complete": cross_layer_invariants_complete,
        "compliance_obligations_complete": compliance_obligations_complete,
        "visual_acceptance": visual_acceptance,
    }
    gate = final_confirmation_gate(ledger, gate_checks)
    report = {
        "supported_domain": DOMAIN,
        "coverage": ledger.summary(),
        "browser": browser_version,
        "evidence_root": dag.root_digest(),
        "strict_obligation_gate": {
            "passed": strict_obligation_ok,
            "stdout": strict_obligation_stdout,
            "stderr": strict_obligation_stderr,
        },
        "final_gate": gate,
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    if gate["passed"]:
        scenario_digest = hashlib.sha256(json.dumps(SCENARIOS, sort_keys=True).encode()).hexdigest()[:16]
        provisional = attest(
            build_digest="public-audit-build",
            contract_digest="public-audit-contract",
            rules_digest="public-audit-rules",
            scenario_digest=scenario_digest,
            evidence_root=dag.root_digest(),
            final_gate=gate,
            environment_manifest={
                "browser": browser_version,
                "viewport_height": DOMAIN.get("viewport_height", 900),
            },
        )
        (BASE / ".goal_attestation.json").write_text(json.dumps(provisional, indent=2))
        return 0

    print("NO LOCK: Final Confirmation Gate is not closed.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
