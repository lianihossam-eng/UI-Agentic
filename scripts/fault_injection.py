"""Fault-injection suite for verification-rule adequacy.

This script emits semantic mutant results only. It does NOT claim authoritative
commit/environment/evidence provenance; capture_current_run_evidence.py attaches
those bindings after the clean A/B replay.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import yaml
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from gvh.extractor import compute_ir
from gvh.verify import verify_all

DOMAIN = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
ROUTE_FILE = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}

MUTANTS = [
    {
        "id": "M1-gap-layout",
        "layer": "geometry",
        "rule": "global.spacing.scale",
        "owner": "GLOBAL",
        "route": "/orders",
        "viewport": 1024,
        "inject": "document.querySelector('[data-testid=\"grid\"]').style.gap='13px'",
        "expect_status": "FAIL",
    },
    {
        "id": "M2-overlay-occlusion",
        "layer": "interaction",
        "rule": "component.button.hit-target",
        "owner": "COMPONENT",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const o=document.createElement('div');
            o.id='mut-overlay';
            o.style.cssText='position:fixed;inset:0;z-index:9999;background:transparent';
            document.body.appendChild(o);
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M3-first-target-size",
        "layer": "interaction",
        "rule": "component.button.hit-target",
        "owner": "COMPONENT",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const b=document.querySelector('[data-testid=\"btn\"]');
            if(b){ b.style.minWidth='20px'; b.style.minHeight='20px'; b.style.width='20px'; b.style.height='20px'; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M4-focus-outside-modal",
        "layer": "accessibility",
        "rule": "MODAL_INTEGRITY",
        "owner": "PAGE",
        "route": "/settings",
        "viewport": 768,
        "open_modal": True,
        "inject": """
            document.querySelector('[data-testid=\"close\"]')?.blur();
            document.activeElement?.blur();
            document.querySelector('[data-testid=\"open-modal\"]')?.focus();
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M5-first-contrast-invalid",
        "layer": "paint",
        "rule": "paint.contrast.text",
        "owner": "PAGE",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const main=document.querySelector('[data-testid="main"]');
            if(main){ main.style.color='#777777'; main.style.backgroundColor='#888888'; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M6-async-layout-shift",
        "layer": "temporal",
        "rule": "temporal.geometry-stable",
        "owner": "PAGE",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const grid=document.querySelector('[data-testid=\"grid\"]');
            if(grid){
                let w=0;
                setInterval(()=>{ grid.style.width=(300+(w++%50))+'px'; },30);
            }
        """,
        "expect_status": "UNKNOWN",
    },
    {
        "id": "M7-breakpoint-incorrect",
        "layer": "geometry",
        "rule": "breakpoint.shell.direction",
        "owner": "FAMILY",
        "route": "/orders",
        "viewport": 375,
        "inject": """
            const style=document.createElement('style');
            style.textContent='.shell{flex-direction:row !important}';
            document.head.appendChild(style);
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M8-second-target-size",
        "layer": "interaction",
        "rule": "component.button.hit-target",
        "owner": "COMPONENT",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const b=document.querySelectorAll('[data-testid=\"btn\"]')[1];
            if(b){ b.style.minWidth='20px'; b.style.minHeight='20px'; b.style.width='20px'; b.style.height='20px'; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M9-late-contrast-invalid",
        "layer": "paint",
        "rule": "paint.contrast.text",
        "owner": "PAGE",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const card=document.querySelectorAll('[data-testid=\"card\"]')[1];
            if(card){ card.style.color='#777777'; card.style.backgroundColor='#888888'; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M10-nonfirst-focus-order",
        "layer": "accessibility",
        "rule": "accessibility.focus-order",
        "owner": "PAGE",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const b=document.querySelectorAll('[data-testid=\"btn\"]')[1];
            if(b){ b.tabIndex=-1; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M11-modal-background-not-inert",
        "layer": "cross-layer",
        "rule": "MODAL_INTEGRITY",
        "owner": "PAGE",
        "route": "/settings",
        "viewport": 768,
        "open_modal": True,
        "inject": "document.querySelector('.shell')?.removeAttribute('inert')",
        "expect_status": "FAIL",
    },
    {
        "id": "M12-mobile-modal-overflow",
        "layer": "geometry",
        "rule": "MODAL_INTEGRITY",
        "owner": "PAGE",
        "route": "/settings",
        "viewport": 320,
        "open_modal": True,
        "inject": """
            const box=document.querySelector('[data-testid=\"modal\"] .box');
            if(box){ box.style.width='480px'; box.style.maxWidth='none'; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M13-mobile-transition-handler-missing",
        "layer": "interaction",
        "rule": "transition:settings-modal",
        "owner": "PAGE",
        "route": "/settings",
        "viewport": 320,
        "mode": "transition-open",
        "inject": """
            const old=document.querySelector('[data-testid=\"open-modal\"]');
            if(old){ old.replaceWith(old.cloneNode(true)); }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M14-escape-transition-handler-missing",
        "layer": "interaction",
        "rule": "transition:settings-modal",
        "owner": "PAGE",
        "route": "/settings",
        "viewport": 320,
        "open_modal": True,
        "mode": "transition-escape-close",
        "inject": """
            const old=document.querySelector('[data-testid=\"modal\"]');
            if(old){ old.replaceWith(old.cloneNode(true)); }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M15-modal-close-removed-from-tab-order",
        "layer": "accessibility",
        "rule": "accessibility.focus-order",
        "owner": "PAGE",
        "route": "/settings",
        "viewport": 375,
        "open_modal": True,
        "inject": """
            const close=document.querySelector('[data-testid=\"close\"]');
            if(close){ close.tabIndex=-1; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M16-horizontal-overflow",
        "layer": "geometry",
        "rule": "geometry.no-horizontal-overflow",
        "owner": "PAGE",
        "route": "/orders",
        "viewport": 375,
        "inject": """
            const grid=document.querySelector('[data-testid=\"grid\"]');
            if(grid){ grid.style.width='800px'; grid.style.maxWidth='none'; }
        """,
        "expect_status": "FAIL",
    },
    {
        "id": "M17-layout-collision",
        "layer": "geometry",
        "rule": "geometry.no-layout-collision",
        "owner": "SECTION",
        "route": "/orders",
        "viewport": 1024,
        "inject": """
            const cards=document.querySelectorAll('[data-testid=\"card\"]');
            if(cards.length>1){ cards[1].style.transform='translateX(-200px)'; }
        """,
        "expect_status": "FAIL",
    },
]


def find_result(findings, rule):
    return next((finding for finding in findings if finding.get("constraint") == rule), None)


def transition_open_status(page):
    opener = page.locator('[data-testid="open-modal"]')
    if opener.count() == 0:
        return "UNKNOWN"
    opener.click()
    evidence = page.evaluate(
        """() => {
          const modal=document.querySelector('[data-testid="modal"]');
          const active=document.activeElement;
          const visible=!!modal && getComputedStyle(modal).display!=='none' && modal.hasAttribute('open');
          return {visible, focusInside:!!modal && !!active && modal.contains(active)};
        }"""
    )
    return "PASS" if evidence["visible"] and evidence["focusInside"] else "FAIL"


def transition_escape_close_status(page):
    page.keyboard.press("Escape")
    evidence = page.evaluate(
        """() => {
          const modal=document.querySelector('[data-testid="modal"]');
          const opener=document.querySelector('[data-testid="open-modal"]');
          const shell=document.querySelector('.shell');
          const active=document.activeElement;
          const visible=!!modal && getComputedStyle(modal).display!=='none' && modal.hasAttribute('open');
          return {
            visible,
            focusReturned:!!opener && active===opener,
            backgroundInert:!!shell && shell.hasAttribute('inert')
          };
        }"""
    )
    return "PASS" if (not evidence["visible"] and evidence["focusReturned"] and not evidence["backgroundInert"]) else "FAIL"


def evaluate(page, mutant):
    if mutant.get("mode") == "transition-open":
        return transition_open_status(page)
    if mutant.get("mode") == "transition-escape-close":
        return transition_escape_close_status(page)
    ir = compute_ir(page)
    finding = find_result(verify_all(ir, page), mutant["rule"])
    return finding.get("status") if finding else "MISSING"


def prepare_state(page, mutant):
    if mutant.get("open_modal"):
        opener = page.locator('[data-testid="open-modal"]')
        if opener.count() == 0:
            return False
        opener.click()
        page.wait_for_timeout(200)
    return True


def fresh_page(browser, mutant):
    context = browser.new_context(
        viewport={"width": mutant["viewport"], "height": DOMAIN.get("viewport_height", 900)}
    )
    page = context.new_page()
    page.goto(ROUTE_FILE[mutant["route"]].as_uri())
    return context, page


def run():
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        version = browser.version
        for mutant in MUTANTS:
            baseline_context, baseline_page = fresh_page(browser, mutant)
            if not prepare_state(baseline_page, mutant):
                baseline_status = "UNKNOWN"
            else:
                baseline_status = evaluate(baseline_page, mutant)

            mutated_context, mutated_page = fresh_page(browser, mutant)
            if not prepare_state(mutated_page, mutant):
                mutated_status = "UNKNOWN"
            else:
                mutated_page.evaluate(mutant["inject"])
                mutated_page.wait_for_timeout(150)
                mutated_status = evaluate(mutated_page, mutant)

            revert_context, revert_page = fresh_page(browser, mutant)
            if not prepare_state(revert_page, mutant):
                revert_status = "UNKNOWN"
            else:
                revert_status = evaluate(revert_page, mutant)

            expected = mutant["expect_status"]
            detected = mutated_status == expected
            if expected in ("FAIL", "UNKNOWN"):
                detected = mutated_status in ("FAIL", "UNKNOWN")
            killed = baseline_status == "PASS" and detected and revert_status == "PASS"
            evidence_key = hashlib.sha256(
                json.dumps(
                    [mutant["id"], mutant["rule"], mutant["viewport"], mutant["route"]],
                    sort_keys=True,
                ).encode()
            ).hexdigest()[:12]
            result = {
                "id": mutant["id"],
                "layer": mutant["layer"],
                "rule_expected": mutant["rule"],
                "owner_expected": mutant["owner"],
                "route": mutant["route"],
                "viewport": mutant["viewport"],
                "baseline_status": baseline_status,
                "mutated_status": mutated_status,
                "expected_status": expected,
                "detected": bool(detected),
                "revert_status": revert_status,
                "revert_ok": revert_status == "PASS",
                "evidence_key": evidence_key,
                "survivor": not killed,
            }
            results.append(result)
            print(
                f"{mutant['id']} baseline={baseline_status} mutated={mutated_status} "
                f"expected={expected} detected={detected} revert={revert_status} killed={killed}"
            )
            baseline_context.close()
            mutated_context.close()
            revert_context.close()
        browser.close()

    by_layer = {}
    for result in results:
        layer = by_layer.setdefault(
            result["layer"], {"total": 0, "detected": 0, "survived": 0}
        )
        layer["total"] += 1
        if result["detected"]:
            layer["detected"] += 1
        if result["survivor"]:
            layer["survived"] += 1

    total = len(results)
    survived = sum(1 for result in results if result["survivor"])
    detected = total - survived
    payload = {
        "raw_mutation_schema": "mutation-semantic-v2",
        "browser": f"chromium@{version}",
        "mutants_total": total,
        "detected": detected,
        "survived": survived,
        "by_layer": by_layer,
        "details": results,
        "survivors": [result for result in results if result["survivor"]],
        "status": "PASS" if survived == 0 else "FAIL",
        "critical_mutants_zero": survived == 0,
    }
    out = BASE / "reports" / "mutation_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote raw semantic mutant results: total={total} survived={survived}")
    print(json.dumps(by_layer, indent=2, sort_keys=True))
    return 0 if survived == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run())
