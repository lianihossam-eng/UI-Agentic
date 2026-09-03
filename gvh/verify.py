from .constraints import check_hard
from .paint import check_paint
from .a11y import check_a11y
from .temporal import check_temporal
from .wcag import trace

ALLOWED_SPACING = {0.0, 4.0, 8.0, 16.0, 24.0, 32.0, 48.0}


def _check_global_spacing(page):
    evidence = page.evaluate(
        """() => {
          const selectors='[data-testid], .shell, .grid, .kpi-row, .card, .kpi, button';
          const props=['gap','rowGap','columnGap','paddingTop','paddingRight','paddingBottom','paddingLeft'];
          const out=[];
          for(const el of document.querySelectorAll(selectors)){
            const s=getComputedStyle(el);
            for(const prop of props){
              const raw=s[prop]; const n=parseFloat(raw);
              if(Number.isFinite(n) && n>0) out.push({
                element: el.dataset.testid || el.className || el.tagName,
                property: prop,
                value: n
              });
            }
          }
          return out;
        }"""
    )
    invalid = [item for item in evidence if round(float(item["value"]), 3) not in ALLOWED_SPACING]
    return {
        "layer": "geometry",
        "constraint": "global.spacing.scale",
        "owner": "GLOBAL",
        "status": "FAIL" if invalid else "PASS",
        "proof_level": "observed",
        "invalid": invalid[:20],
        "sample_count": len(evidence),
    }


def _check_modal_integrity(page):
    modal = page.locator('[data-testid="modal"]')
    if modal.count() == 0:
        return {
            "layer": "interaction",
            "constraint": "MODAL_INTEGRITY",
            "owner": "PAGE",
            "status": "UNKNOWN",
            "reason": "modal-not-present",
            "requires_layers": ["geometry", "interaction", "accessibility"],
        }
    evidence = modal.evaluate(
        """m => {
          const s=getComputedStyle(m); const r=m.getBoundingClientRect();
          const dialog=m.matches('[role="dialog"]') ? m : m.querySelector('[role="dialog"]');
          const ariaModal=dialog?.getAttribute('aria-modal') === 'true';
          const active=document.activeElement;
          const dialogInside=m.querySelector('[role="dialog"]');
          const activeTestId=active?.getAttribute('data-testid');
          const focusInside=!!active && (m.contains(active) || (dialogInside && dialogInside.contains(active)) || activeTestId==='close');
          const centerHit=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
          const centerOwned=!!centerHit && (centerHit===m || m.contains(centerHit));
          const sidebar=document.querySelector('[data-testid="sidebar"]');
          let backgroundBlocked=true;
          if(sidebar){
            const b=sidebar.getBoundingClientRect();
            const hit=document.elementFromPoint(b.x+b.width/2, b.y+Math.min(40,b.height/2));
            backgroundBlocked=!!hit && (hit===m || m.contains(hit));
          }
          return {
            visible:s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0,
            fixed:s.position==='fixed',
            ariaModal,
            focusInside,
            centerOwned,
            backgroundBlocked,
            activeTestId,
            isClose: activeTestId==='close'
          };
        }"""
    )
    # Strict MODAL_INTEGRITY per audit 2026-09-03T08:04: focusInside is mandatory for open state.
    # If focus observability is missing, emit UNKNOWN rather than lenient PASS.
    required_keys = ("visible", "fixed", "ariaModal", "focusInside", "centerOwned", "backgroundBlocked")
    if any(evidence.get(k) is None for k in required_keys):
        return {
            "layer": "interaction",
            "constraint": "MODAL_INTEGRITY",
            "owner": "PAGE",
            "status": "UNKNOWN",
            "reason": "modal-focus-not-observable",
            "requires_layers": ["geometry", "interaction", "accessibility"],
            "evidence_bundle": evidence,
        }
    is_open = evidence.get("visible") is True
    if is_open:
        passed = all(evidence.get(key) is True for key in required_keys)
    else:
        passed = (
            evidence.get("visible") is False
            and evidence.get("fixed") is True
            and evidence.get("ariaModal") is True
            and evidence.get("focusInside") is False
            and evidence.get("backgroundBlocked") is False
        )
    return {
        "layer": "interaction",
        "constraint": "MODAL_INTEGRITY",
        "owner": "PAGE",
        "status": "PASS" if passed else "FAIL",
        "proof_level": "observed",
        "requires_layers": ["geometry", "interaction", "accessibility"],
        "evidence_bundle": evidence,
    }


def verify_all(ir, page=None):
    findings = []

    geo = check_hard(ir)
    if geo:
        for violation in geo:
            findings.append({"layer": "geometry", "proof_level": "observed", **violation})
    else:
        findings.append({
            "layer": "geometry",
            "constraint": "group.uniform_gap",
            "owner": "PAGE",
            "status": "PASS",
            "proof_level": "observed",
        })

    if page is None:
        return findings

    # Modal integrity must be captured before a11y mutates focus (Tab/blur)
    findings.append(_check_modal_integrity(page))

    findings.append(_check_global_spacing(page))

    for finding in check_paint(ir):
        findings.append({
            "layer": "paint",
            "proof_level": "observed",
            **finding,
            "wcag": trace(finding["constraint"], finding),
        })

    buttons = [
        value for value in ir["nodes"].values()
        if value.get("visible") and (value.get("testid") == "btn" or value.get("tag") == "button")
    ]
    if buttons:
        value = buttons[0]
        hit_ok = value.get("hit", {}).get("hitOk", False)
        width, height = value["box"][2], value["box"][3]
        findings.append({
            "layer": "interaction",
            "constraint": "component.button.hit-target",
            "owner": "COMPONENT",
            "status": "PASS" if (width >= 44 and height >= 44 and hit_ok) else "FAIL",
            "actual": [width, height],
            "hit": hit_ok,
            "proof_level": "observed",
        })
        visible = value["visibleRegion"][2] * value["visibleRegion"][3] > 0
        operable = width >= 44 and height >= 44 and hit_ok and visible
        findings.append({
            "layer": "interaction",
            "constraint": "TARGET_OPERABLE",
            "owner": "COMPONENT",
            "status": "PASS" if operable else "FAIL",
            "requires_layers": ["geometry", "interaction"],
            "proof_level": "observed",
            "evidence_bundle": {"hit": hit_ok, "size": [width, height], "visible": visible},
        })
    else:
        for constraint in ("component.button.hit-target", "TARGET_OPERABLE"):
            findings.append({
                "layer": "interaction",
                "constraint": constraint,
                "owner": "COMPONENT",
                "status": "UNKNOWN",
                "reason": "no-visible-button",
            })

    for finding in check_a11y(page, ir):
        payload = {"layer": "accessibility", "proof_level": "observed", **finding}
        payload["wcag"] = trace(finding["constraint"], finding)
        findings.append(payload)

    for finding in check_temporal(page):
        findings.append({"layer": "temporal", **finding})

    return findings
