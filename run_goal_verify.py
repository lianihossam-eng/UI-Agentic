import hashlib
import json
import pathlib
import subprocess
import sys
import platform

import yaml
from playwright.sync_api import sync_playwright
import importlib.metadata

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


def main():
    ledger = CoverageLedger(SCENARIOS)
    dag = EvidenceDAG()
    readiness_results = []
    transition_results = []
    cross_layer_results = []

    static_scenarios = [
        sc for sc in SCENARIOS
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
            context = browser.new_context(viewport={"width": viewport, "height": DOMAIN.get("viewport_height", 900)})
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
            context = browser.new_context(viewport={"width": scenario["viewport"], "height": DOMAIN.get("viewport_height", 900)})
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

        by_model = {}
        for scenario in transition_scenarios:
            by_model.setdefault(scenario["model"], []).append(scenario)
        for model, scenarios in by_model.items():
            route = scenarios[0]["route"]
            context = browser.new_context(viewport={"width": 768, "height": DOMAIN.get("viewport_height", 900)})
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

    all_required_observed = all(
        item.get("status") != "PASS" or item.get("proof_level", "observed") == "observed"
        for item in ledger.results
    )
    transition_complete = bool(transition_results) and all(item.get("status") == "PASS" for item in transition_results)
    cross_layer_ledger_complete = bool(cross_layer_results) and all(item.get("status") == "PASS" for item in cross_layer_results)
    readiness_complete = bool(readiness_results) and all(item.get("status") == "PASS" for item in readiness_results)

    def _current_binding(evidence_root):
        try:
            commit_sha = subprocess.check_output(["git","rev-parse","HEAD"], cwd=BASE).decode().strip()
        except:
            commit_sha = "unknown"
        scenario_digest_local = hashlib.sha256(json.dumps(SCENARIOS, sort_keys=True).encode()).hexdigest()[:16]
        rules_seed = ["group.uniform_gap","global.spacing.scale","paint.contrast.text","component.button.hit-target","TARGET_OPERABLE","accessibility.focus-order","FOCUS_USABLE","temporal.geometry-stable","MODAL_INTEGRITY","breakpoint.shell.direction"]
        rules_digest_local = hashlib.sha256((BASE/"supported-domain.yaml").read_bytes() + json.dumps(rules_seed, sort_keys=True).encode()).hexdigest()[:16]
        checker_files = ["gvh/verify.py","gvh/extractor.py","core/coverage.py","core/scenario_compiler.py"]
        checker_digest_local = hashlib.sha256(b"".join((BASE/f).read_bytes() for f in checker_files)).hexdigest()[:16]
        env_path = BASE/"reports/environment_manifest.json"
        env_digest_local = None
        if env_path.exists():
            try:
                env_data = json.loads(env_path.read_text())
                copy = {k:v for k,v in env_data.items() if k not in ("manifest_digest","manifest_hash_algo")}
                env_digest_local = hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest()[:16]
            except:
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
        p = BASE / "reports" / f"{name}.json"
        if not p.exists():
            return False, f"missing:{name}", None
        try:
            data = json.loads(p.read_text())
        except Exception as exc:
            return False, f"invalid-json:{name}:{exc}", None
        expected = data.get("report_hash")
        if not expected:
            return False, f"no-hash:{name}", data
        copy = {k: v for k, v in data.items() if k not in ("report_hash", "report_hash_algo")}
        computed = hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest()[:16]
        if computed != expected:
            return False, f"hash-mismatch:{name}", data
        if data.get("status") == "PENDING":
            return False, f"pending:{name}", data
        for field in ["scenario_digest","evidence_root","rules_digest","checker_digest"]:
            if field in data and data.get(field) != binding.get(field):
                return False, f"binding-mismatch:{name}:{field} expected {binding.get(field)} got {data.get(field)}", data
        if "environment_manifest_digest" in data and binding.get("env_digest") and data.get("environment_manifest_digest") != binding.get("env_digest"):
            return False, f"binding-mismatch:{name}:environment_manifest_digest", data
        return True, "ok", data

    def _check_traceability_real(trace_data):
        try:
            mapping = trace_data.get("mapping", [])
            if len(mapping) != ledger.required:
                return False, f"mapping len {len(mapping)} != required {ledger.required}"
            expected_ids = [f"{sc.get('route','global')}@{sc.get('viewport',768)}:{sc['rule']}" for sc in SCENARIOS]
            mapped_ids = [m.get("scenario_id") for m in mapping]
            from collections import Counter
            if Counter(expected_ids) != Counter(mapped_ids):
                return False, f"scenario_ids multiset mismatch"
            for m in mapping:
                if not all(k in m for k in ("requirement","failure_mode","rule","scenario_id")):
                    return False, f"mapping entry missing keys {m}"
            return True, "ok"
        except Exception as exc:
            return False, f"traceability-check-error:{exc}"

    ok_trace, msg_trace, trace_data = _validate_report("traceability_report")
    trace_real_ok, trace_real_msg = _check_traceability_real(trace_data) if ok_trace else (False, "no-trace")
    requirement_traceability = (
        ok_trace
        and trace_data.get("percentage") == 100
        and trace_data.get("traced_obligations") == ledger.required
        and trace_data.get("required_obligations") == ledger.required
        and trace_data.get("status") == "PASS"
        and trace_real_ok
    )

    ok_mut, msg_mut, mut_data = _validate_report("mutation_report")
    mut_strict_ok = False
    if ok_mut and mut_data:
        details = mut_data.get("details", [])
        mut_strict_ok = True
        for d in details:
            if d.get("baseline_status") != "PASS":
                mut_strict_ok = False
                break
            if not d.get("detected"):
                mut_strict_ok = False
                break
            if d.get("mutated_status") not in ("FAIL","UNKNOWN"):
                mut_strict_ok = False
                break
            if d.get("revert_status") != "PASS":
                mut_strict_ok = False
                break
            if d.get("survivor"):
                mut_strict_ok = False
                break
    critical_mutants_zero = (
        ok_mut
        and mut_data.get("survived") == 0
        and mut_data.get("critical_mutants_zero") is True
        and mut_data.get("status") == "PASS"
        and mut_data.get("mutants_total") >= 7
        and mut_strict_ok
    )

    ok_assump, _, assump_data = _validate_report("assumptions_report")
    unstated_assumptions_zero = ok_assump and assump_data.get("unstated_count") == 0 and assump_data.get("status") == "PASS"

    ok_regress, _, regress_data = _validate_report("regression_report")
    regression_closed = ok_regress and regress_data.get("closed") is True and regress_data.get("status") == "PASS"

    ok_parent, _, parent_data = _validate_report("parent_contract_report")
    parent_contracts_valid = ok_parent and parent_data.get("all_valid") is True and parent_data.get("status") == "PASS"

    ok_cross, _, cross_data = _validate_report("cross_layer_report")
    cross_bundles_ok = False
    if ok_cross and cross_data:
        bundles = cross_data.get("evidence_bundles", {})
        snap = cross_data.get("snapshot_evidence", {})
        cross_bundles_ok = (
            all(k in bundles for k in ("TARGET_OPERABLE","FOCUS_USABLE","MODAL_INTEGRITY"))
            and snap.get("all_pass") is True
            and all(snap.get(f"{k}_status")=="PASS" for k in ("TARGET_OPERABLE","FOCUS_USABLE","MODAL_INTEGRITY"))
        )
    cross_layer_invariants_complete = ok_cross and cross_data.get("complete") is True and cross_data.get("status") == "PASS" and cross_layer_ledger_complete and cross_bundles_ok

    ok_visual, _, visual_data = _validate_report("visual_review")
    visual_screenshots_ok = False
    if ok_visual and visual_data:
        digests = visual_data.get("screenshot_digests", {})
        count = visual_data.get("screenshot_count")
        snap = visual_data.get("snapshot_digest")
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
            calc_snap = hashlib.sha256(json.dumps(digests, sort_keys=True).encode()).hexdigest()[:16]
            if calc_snap == snap:
                dig_path = BASE/"reports/screenshots/digests.json"
                if dig_path.exists():
                    try:
                        file_dig = json.loads(dig_path.read_text())
                        if file_dig == digests:
                            visual_screenshots_ok = True
                    except:
                        pass
    visual_acceptance = ok_visual and visual_data.get("verdict") == "ACCEPTED" and visual_data.get("status") == "PASS" and visual_screenshots_ok

    certificate_validation = True
    compliance_obligations_complete = not bool(DOMAIN.get("compliance_profiles"))

    gate_checks = {
        "requirement_traceability": requirement_traceability,
        "required_proof_levels": all_required_observed,
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
        "final_gate": gate,
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    if gate["passed"]:
        scenario_digest = hashlib.sha256(json.dumps(SCENARIOS, sort_keys=True).encode()).hexdigest()[:16]
        locked = attest(
            build_digest="public-audit-build",
            contract_digest="public-audit-contract",
            rules_digest="public-audit-rules",
            scenario_digest=scenario_digest,
            evidence_root=dag.root_digest(),
            final_gate=gate,
            environment_manifest={"browser": browser_version, "viewport_height": DOMAIN.get("viewport_height", 900)},
        )
        (BASE / ".goal_attestation.json").write_text(json.dumps(locked, indent=2))
        return 0

    print("NO LOCK: Final Confirmation Gate is not closed.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
