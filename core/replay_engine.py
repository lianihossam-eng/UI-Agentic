"""State-aware browser replay engine for the executable Supported Domain.

This module is the only browser measurement primitive used to build current-run
proof evidence. It applies the declared UI state before readiness/measurement,
groups compatible obligations to avoid inconsistent snapshots, and records one
result whose constraint must equal each compiled rule.
"""
from __future__ import annotations

import hashlib
import pathlib

from playwright.sync_api import sync_playwright

from core.coverage import CoverageLedger, EvidenceDAG, measurement_readiness
from core.measurement_kernel import measurement_kernel_digest
from gvh.extractor import compute_ir
from gvh.verify import verify_all


def _file_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _result_for(findings: list[dict], rule: str) -> dict:
    matches = [item for item in findings if item.get("constraint") == rule]
    if len(matches) != 1:
        return {
            "constraint": rule,
            "status": "UNKNOWN",
            "proof_level": "observed",
            "reason": (
                "checker-produced-no-result"
                if not matches
                else f"checker-produced-ambiguous-results:{len(matches)}"
            ),
        }
    result = dict(matches[0])
    if result.get("constraint") != rule:
        return {
            "constraint": rule,
            "status": "UNKNOWN",
            "proof_level": "observed",
            "reason": "checker-constraint-mismatch",
        }
    return result


def _render_environment(page, domain: dict, state: str) -> dict:
    observed = page.evaluate(
        """() => ({
          width: window.innerWidth,
          height: window.innerHeight,
          dpr: window.devicePixelRatio,
          documentLanguage: document.documentElement.lang || '',
          documentDirection: getComputedStyle(document.documentElement).direction || document.dir || 'ltr'
        })"""
    )
    return {
        "viewport_width": observed["width"],
        "viewport_height": observed["height"],
        "device_pixel_ratio": observed["dpr"],
        "document_language": observed["documentLanguage"],
        "document_direction": observed["documentDirection"],
        "declared_locale_direction": list(domain.get("locales_directions", [])),
        "declared_zoom_dpr": list(domain.get("zoom_dpr", [])),
        "declared_inputs": list(domain.get("input_modalities", [])),
        "state": state,
    }


def _apply_state(page, state: str | None) -> tuple[bool, str | None]:
    if state in (None, "default"):
        return True, None
    if state == "modal-open":
        opener = page.locator('[data-testid="open-modal"]')
        if opener.count() != 1:
            return False, "modal-opener-missing-or-ambiguous"
        try:
            opener.click()
            page.wait_for_function(
                """() => {
                  const modal=document.querySelector('[data-testid="modal"]');
                  if(!modal) return false;
                  const s=getComputedStyle(modal);
                  const r=modal.getBoundingClientRect();
                  return modal.hasAttribute('open') && s.display!=='none' &&
                         s.visibility!=='hidden' && r.width>0 && r.height>0;
                }"""
            )
        except Exception as exc:
            return False, f"modal-open-setup-failed:{exc}"
        return True, None
    return False, f"unsupported-state:{state}"


def _execute_transition(page, transition: dict) -> dict:
    action = transition.get("action", "")
    try:
        if action.startswith("click:"):
            selector = action.split(":", 1)[1]
            locator = page.locator(selector)
            if locator.count() != 1:
                return {
                    "constraint": "transition",
                    "status": "UNKNOWN",
                    "reason": f"transition-target-missing-or-ambiguous:{selector}",
                    "proof_level": "observed",
                }
            locator.click()
        elif action.startswith("press:"):
            key = action.split(":", 1)[1]
            if not key:
                return {
                    "constraint": "transition",
                    "status": "UNKNOWN",
                    "reason": "transition-key-missing",
                    "proof_level": "observed",
                }
            page.keyboard.press(key)
        else:
            return {
                "constraint": "transition",
                "status": "UNKNOWN",
                "reason": f"unsupported-transition-action:{action}",
                "proof_level": "observed",
            }
    except Exception as exc:
        return {
            "constraint": "transition",
            "status": "FAIL",
            "reason": f"transition-action-failed:{exc}",
            "proof_level": "observed",
        }

    assertion = transition.get("assertion")
    evidence = page.evaluate(
        """() => {
          const modal=document.querySelector('[data-testid="modal"]');
          const opener=document.querySelector('[data-testid="open-modal"]');
          const shell=document.querySelector('.shell');
          const active=document.activeElement;
          const visible=modal ? getComputedStyle(modal).display!=='none' &&
            getComputedStyle(modal).visibility!=='hidden' && modal.hasAttribute('open') : false;
          return {
            modalOpen: visible,
            focusInsideModal: !!modal && !!active && modal.contains(active),
            focusReturnedToOpener: !!opener && active===opener,
            backgroundInert: !!shell && shell.hasAttribute('inert')
          };
        }"""
    )
    if assertion == "modal-open":
        passed = (
            evidence["modalOpen"]
            and evidence["focusInsideModal"]
            and evidence["backgroundInert"]
        )
    elif assertion == "modal-closed":
        passed = (
            (not evidence["modalOpen"])
            and evidence["focusReturnedToOpener"]
            and (not evidence["backgroundInert"])
        )
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


def replay(
    *,
    domain: dict,
    scenarios: list[dict],
    route_files: dict[str, pathlib.Path],
    capture_screenshots: bool = False,
    screenshot_dir: pathlib.Path | None = None,
) -> dict:
    ledger = CoverageLedger(scenarios)
    dag = EvidenceDAG()
    records: list[dict] = []
    readiness_results: list[dict] = []
    transition_results: list[dict] = []
    cross_layer_results: list[dict] = []
    measurement_digest = measurement_kernel_digest()

    def record(
        scenario: dict,
        result: dict,
        browser_version: str,
        readiness: dict,
        rendered_environment: dict,
    ) -> None:
        if result.get("constraint") != scenario.get("rule"):
            result = {
                "constraint": scenario.get("rule"),
                "status": "UNKNOWN",
                "proof_level": "observed",
                "reason": (
                    "result-constraint-mismatch:"
                    f"{result.get('constraint')}!={scenario.get('rule')}"
                ),
            }
        ledger.record(result)
        route = scenario.get("route", "global")
        code_digest = _file_hash(route_files[route]) if route in route_files else "no-route"
        environment = {
            **rendered_environment,
            "browser": browser_version,
            "measurement_kernel_digest": measurement_digest,
            "readiness": readiness.get("checks", {}),
        }
        key = dag.key(
            code_digest,
            "contract-public-audit-v1",
            scenario["rule"],
            scenario,
            browser_version,
            measurement_digest,
            environment,
        )
        dag.put(
            key,
            {
                "scenario": scenario,
                "result": result,
                "readiness": readiness,
                "rendered_environment": rendered_environment,
                "measurement_kernel_digest": measurement_digest,
            },
        )
        records.append(
            {
                "scenario": scenario,
                "result": result,
                "evidence_key": key,
                "readiness_status": readiness.get("status"),
                "rendered_environment": rendered_environment,
                "measurement_kernel_digest": measurement_digest,
            }
        )

    rendered = [sc for sc in scenarios if not sc["rule"].startswith("transition:")]
    transitions = [sc for sc in scenarios if sc["rule"].startswith("transition:")]

    if capture_screenshots:
        if screenshot_dir is None:
            raise ValueError("screenshot_dir is required when capture_screenshots=True")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        for old in screenshot_dir.glob("*.png"):
            old.unlink()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        browser_version = f"chromium@{browser.version}"

        groups: dict[tuple[str, int, str], list[dict]] = {}
        for scenario in rendered:
            key = (
                scenario.get("route", "/orders"),
                scenario.get("viewport", 768),
                scenario.get("state", "default"),
            )
            groups.setdefault(key, []).append(scenario)

        for (route, viewport, state), group in groups.items():
            context = browser.new_context(
                viewport={"width": viewport, "height": domain.get("viewport_height", 900)}
            )
            page = context.new_page()
            page.goto(route_files[route].as_uri())

            state_ok, state_reason = _apply_state(page, state)
            rendered_environment = _render_environment(page, domain, state)
            if not state_ok:
                readiness = {"status": "UNKNOWN", "checks": {}, "blockers": [state_reason]}
            else:
                readiness = measurement_readiness(page)
            readiness_results.append(readiness)

            if readiness.get("status") != "PASS":
                for scenario in group:
                    record(
                        scenario,
                        {
                            "constraint": scenario["rule"],
                            "status": "UNKNOWN",
                            "proof_level": "observed",
                            "reason": "measurement-readiness-not-satisfied",
                            "readiness": readiness,
                        },
                        browser_version,
                        readiness,
                        rendered_environment,
                    )
                context.close()
                continue

            ir = compute_ir(page)
            findings = verify_all(ir, page)
            for scenario in group:
                result = _result_for(findings, scenario["rule"])
                if scenario["rule"] in ("TARGET_OPERABLE", "FOCUS_USABLE", "MODAL_INTEGRITY"):
                    cross_layer_results.append({"scenario": scenario, "result": result})
                record(scenario, result, browser_version, readiness, rendered_environment)

            if capture_screenshots and state == "default":
                out = screenshot_dir / f"{route.strip('/')}-{viewport}.png"
                page.screenshot(path=str(out), full_page=True)
            context.close()

        # Every transition is an independent proof obligation. Its declared
        # source state is established on a fresh page before readiness and the
        # event, so branching exits from modal-open do not depend on list order.
        for scenario in transitions:
            route = scenario["route"]
            viewport = scenario.get("viewport", 768)
            transition = scenario["transition"]
            source_state = transition.get("from", "default")
            context = browser.new_context(
                viewport={"width": viewport, "height": domain.get("viewport_height", 900)}
            )
            page = context.new_page()
            page.goto(route_files[route].as_uri())
            state_ok, state_reason = _apply_state(page, source_state)
            rendered_environment = _render_environment(page, domain, source_state)
            if not state_ok:
                readiness = {"status": "UNKNOWN", "checks": {}, "blockers": [state_reason]}
            else:
                readiness = measurement_readiness(page)
            readiness_results.append(readiness)

            if readiness.get("status") != "PASS":
                result = {
                    "constraint": scenario["rule"],
                    "status": "UNKNOWN",
                    "proof_level": "observed",
                    "reason": "measurement-readiness-not-satisfied",
                }
            else:
                result = _execute_transition(page, transition)
                result["constraint"] = scenario["rule"]
            transition_results.append({"scenario": scenario, "result": result})
            record(scenario, result, browser_version, readiness, rendered_environment)
            context.close()

        browser.close()

    return {
        "browser": browser_version,
        "coverage": ledger.summary(),
        "evidence_root": dag.root_digest(),
        "measurement_kernel_digest": measurement_digest,
        "records": records,
        "readiness": readiness_results,
        "transitions": transition_results,
        "cross_layer": cross_layer_results,
    }
