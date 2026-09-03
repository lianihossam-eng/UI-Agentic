import hashlib
import json
import pathlib
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
    cross_layer_complete = bool(cross_layer_results) and all(item.get("status") == "PASS" for item in cross_layer_results)
    readiness_complete = bool(readiness_results) and all(item.get("status") == "PASS" for item in readiness_results)

    # External gates intentionally remain false until independent evidence is supplied.
    gate_checks = {
        "requirement_traceability": False,
        "required_proof_levels": all_required_observed,
        "certificate_validation": True,  # no BOUNDED/CERTIFIED obligation in current executable demo domain
        "measurement_readiness": readiness_complete,
        "critical_mutants_zero": False,
        "unstated_assumptions_zero": False,
        "regression_closed": False,
        "parent_contracts_valid": False,
        "state_transitions_complete": transition_complete,
        "cross_layer_invariants_complete": cross_layer_complete,
        "compliance_obligations_complete": not bool(DOMAIN.get("compliance_profiles")),
        "visual_acceptance": False,
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
