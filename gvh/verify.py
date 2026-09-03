from .constraints import check_hard
from .paint import check_paint
from .interaction import check_interaction
from .a11y import check_a11y
from .temporal import check_temporal
from .wcag import trace

ALLOWED_SPACING = {0.0, 4.0, 8.0, 16.0, 24.0, 32.0, 48.0}


def _check_global_spacing(page):
    evidence = page.evaluate(
        """() => {
          const selectors='[data-testid], .shell, .grid, .kpi-row, .card, .kpi, button';
          const props=[
            'gap','rowGap','columnGap',
            'paddingTop','paddingRight','paddingBottom','paddingLeft',
            'marginTop','marginRight','marginBottom','marginLeft'
          ];
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
    if not evidence:
        status = "UNKNOWN"
        reason = "no-positive-spacing-measurements"
    elif invalid:
        status = "FAIL"
        reason = None
    else:
        status = "PASS"
        reason = None
    result = {
        "layer": "geometry",
        "constraint": "global.spacing.scale",
        "owner": "GLOBAL",
        "status": status,
        "proof_level": "observed",
        "invalid": invalid[:20],
        "sample_count": len(evidence),
    }
    if reason:
        result["reason"] = reason
    return result


def _check_horizontal_overflow(page):
    """Fail closed on unintended horizontal viewport overflow.

    Vertical document growth is intentionally allowed; this rule only checks the
    horizontal axis. Both document scroll width and visible instrumented boxes
    must fit the viewport within a 1px rendering tolerance.
    """
    evidence = page.evaluate(
        """() => {
          const tolerance=1;
          const width=window.innerWidth;
          const doc=document.documentElement;
          const body=document.body;
          const scrollWidth=Math.max(doc?.scrollWidth||0, body?.scrollWidth||0);
          const visible=[];
          const offenders=[];
          for(const el of document.querySelectorAll('[data-testid]')){
            const s=getComputedStyle(el); const r=el.getBoundingClientRect();
            const isVisible=s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity)!==0 && r.width>0 && r.height>0;
            if(!isVisible) continue;
            const item={
              testid:el.dataset.testid||null,
              left:r.left,
              right:r.right,
              width:r.width,
              position:s.position
            };
            visible.push(item);
            if(r.left < -tolerance || r.right > width+tolerance) offenders.push(item);
          }
          return {
            viewportWidth:width,
            documentScrollWidth:scrollWidth,
            visibleCount:visible.length,
            documentOverflow:scrollWidth > width+tolerance,
            offenders
          };
        }"""
    )
    if evidence.get("visibleCount", 0) <= 0:
        status = "UNKNOWN"
        reason = "no-visible-instrumented-elements"
    else:
        failed = bool(evidence.get("documentOverflow") or evidence.get("offenders"))
        status = "FAIL" if failed else "PASS"
        reason = None
    result = {
        "layer": "geometry",
        "constraint": "geometry.no-horizontal-overflow",
        "owner": "PAGE",
        "status": status,
        "proof_level": "observed",
        "evidence_bundle": evidence,
        "failure_count": len(evidence.get("offenders") or []) + (1 if evidence.get("documentOverflow") else 0),
    }
    if reason:
        result["reason"] = reason
    return result


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
          const dr=dialog?.getBoundingClientRect();
          const ariaModal=dialog?.getAttribute('aria-modal') === 'true';
          const active=document.activeElement;
          const activeTestId=active?.getAttribute('data-testid');
          const focusInside=!!active && m.contains(active);
          const centerHit=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
          const centerOwned=!!centerHit && (centerHit===m || m.contains(centerHit));
          const shell=document.querySelector('.shell');
          const backgroundInert=!!shell && shell.hasAttribute('inert');
          const sidebar=document.querySelector('[data-testid="sidebar"]');
          let backgroundBlocked=true;
          if(sidebar){
            const b=sidebar.getBoundingClientRect();
            const hit=document.elementFromPoint(b.x+b.width/2, b.y+Math.min(40,b.height/2));
            backgroundBlocked=!!hit && (hit===m || m.contains(hit));
          }
          const dialogContained=!!dr && dr.width>0 && dr.height>0 &&
            dr.left>=-0.5 && dr.top>=-0.5 &&
            dr.right<=window.innerWidth+0.5 && dr.bottom<=window.innerHeight+0.5;
          return {
            visible:s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0,
            fixed:s.position==='fixed',
            ariaModal,
            focusInside,
            centerOwned,
            backgroundBlocked,
            backgroundInert,
            dialogContained,
            activeTestId
          };
        }"""
    )

    is_open = evidence.get("visible") is True
    if is_open:
        page.keyboard.press("Tab")
        tab_inside = page.evaluate(
            """() => {
              const m=document.querySelector('[data-testid="modal"]');
              return !!m && !!document.activeElement && m.contains(document.activeElement);
            }"""
        )
        page.keyboard.press("Shift+Tab")
        shift_tab_inside = page.evaluate(
            """() => {
              const m=document.querySelector('[data-testid="modal"]');
              return !!m && !!document.activeElement && m.contains(document.activeElement);
            }"""
        )
        evidence["tabContained"] = bool(tab_inside)
        evidence["shiftTabContained"] = bool(shift_tab_inside)
        evidence["keyboardContained"] = bool(tab_inside and shift_tab_inside)

        required_keys = (
            "visible",
            "fixed",
            "ariaModal",
            "focusInside",
            "centerOwned",
            "backgroundBlocked",
            "backgroundInert",
            "dialogContained",
            "keyboardContained",
        )
        if any(evidence.get(key) is None for key in required_keys):
            status = "UNKNOWN"
            reason = "modal-required-evidence-not-observable"
        else:
            status = "PASS" if all(evidence.get(key) is True for key in required_keys) else "FAIL"
            reason = None
    else:
        required_closed = ("fixed", "ariaModal")
        if any(evidence.get(key) is None for key in required_closed):
            status = "UNKNOWN"
            reason = "closed-modal-evidence-not-observable"
        else:
            passed = (
                evidence.get("visible") is False
                and evidence.get("fixed") is True
                and evidence.get("ariaModal") is True
                and evidence.get("focusInside") is False
                and evidence.get("backgroundBlocked") is False
                and evidence.get("backgroundInert") is False
            )
            status = "PASS" if passed else "FAIL"
            reason = None

    result = {
        "layer": "interaction",
        "constraint": "MODAL_INTEGRITY",
        "owner": "PAGE",
        "status": status,
        "proof_level": "observed",
        "requires_layers": ["geometry", "interaction", "accessibility"],
        "evidence_bundle": evidence,
    }
    if reason:
        result["reason"] = reason
    return result


def _check_breakpoint(page, ir):
    """Breakpoint policy: shell flex direction column <=767 else row."""
    try:
        vp = ir.get("viewport", {}).get(
            "width",
            page.viewport_size.get("width", 1024) if hasattr(page, "viewport_size") else 1024,
        )
    except Exception:
        vp = 1024
    evidence = page.evaluate(
        """() => {
          const shell=document.querySelector('.shell');
          if(!shell) return {found:false};
          const s=getComputedStyle(shell);
          return {found:true, flexDirection:s.flexDirection, display:s.display};
        }"""
    )
    if not evidence.get("found"):
        return {
            "layer": "geometry",
            "constraint": "breakpoint.shell.direction",
            "owner": "FAMILY",
            "status": "UNKNOWN",
            "reason": "shell-not-found",
            "proof_level": "observed",
        }
    expected = "column" if vp <= 767 else "row"
    actual = evidence.get("flexDirection")
    return {
        "layer": "geometry",
        "constraint": "breakpoint.shell.direction",
        "owner": "FAMILY",
        "status": "PASS" if actual == expected else "FAIL",
        "proof_level": "observed",
        "expected": expected,
        "actual": actual,
        "viewport": vp,
        "evidence_bundle": evidence,
    }


def verify_all(ir, page=None):
    findings = []

    geo = check_hard(ir)
    gap_findings = [item for item in geo if item.get("constraint") == "group.uniform_gap"]
    if not gap_findings:
        findings.append(
            {
                "layer": "geometry",
                "constraint": "group.uniform_gap",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "uniform-gap-checker-produced-no-result",
                "proof_level": "observed",
            }
        )
    for item in geo:
        findings.append({"layer": "geometry", "proof_level": "observed", **item})

    if page is None:
        return findings

    findings.append(_check_modal_integrity(page))
    findings.append(_check_global_spacing(page))
    findings.append(_check_horizontal_overflow(page))
    findings.append(_check_breakpoint(page, ir))

    for finding in check_paint(ir):
        findings.append(
            {
                "layer": "paint",
                "proof_level": "observed",
                **finding,
                "wcag": trace(finding["constraint"], finding),
            }
        )

    findings.extend(check_interaction(ir))

    for finding in check_a11y(page, ir):
        payload = {"layer": "accessibility", "proof_level": "observed", **finding}
        payload["wcag"] = trace(finding["constraint"], finding)
        findings.append(payload)

    for finding in check_temporal(page):
        findings.append({"layer": "temporal", **finding})

    return findings
