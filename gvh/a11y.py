"""Accessibility checks — real keyboard order + cross-layer focus evidence."""


def check_a11y(page, ir):
    expected = page.evaluate(
        """() => [...document.querySelectorAll(
          'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )].filter(e => {
          const s=getComputedStyle(e); const r=e.getBoundingClientRect();
          return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
        }).map(e => e.dataset.testid || e.tagName.toLowerCase())"""
    )

    page.evaluate("() => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); }")
    actual = []
    for _ in range(min(len(expected), 12)):
        page.keyboard.press("Tab")
        active = page.evaluate(
            """() => {
              const e=document.activeElement;
              return e ? (e.dataset.testid || e.tagName.toLowerCase()) : null;
            }"""
        )
        actual.append(active)

    findings = []
    if not expected:
        findings.append({
            "constraint": "accessibility.focus-order",
            "owner": "PAGE",
            "status": "UNKNOWN",
            "reason": "no-focusable-elements",
        })
    else:
        prefix = expected[: len(actual)]
        findings.append({
            "constraint": "accessibility.focus-order",
            "owner": "PAGE",
            "status": "PASS" if actual == prefix else "FAIL",
            "expected": prefix,
            "actual": actual,
        })

    button = page.locator("button:not([disabled])").first
    if button.count() == 0:
        findings.append({
            "constraint": "FOCUS_USABLE",
            "owner": "COMPONENT",
            "status": "UNKNOWN",
            "reason": "no-button",
            "requires_layers": ["geometry", "accessibility", "paint"],
        })
        return findings

    button.focus()
    evidence = button.evaluate(
        """e => {
          const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
          const cx=r.x+r.width/2, cy=r.y+r.height/2;
          const hit=document.elementFromPoint(cx,cy);
          const outline=parseFloat(s.outlineWidth||'0')>0 && s.outlineStyle!=='none';
          const shadow=s.boxShadow && s.boxShadow!=='none';
          return {
            focused: document.activeElement===e,
            visible: s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0,
            notObscured: !!hit && (hit===e || e.contains(hit)),
            focusIndicator: !!(outline || shadow),
            size:[r.width,r.height],
            outlineStyle:s.outlineStyle,
            outlineWidth:s.outlineWidth,
            boxShadow:s.boxShadow
          };
        }"""
    )
    passed = (
        evidence.get("focused")
        and evidence.get("visible")
        and evidence.get("notObscured")
        and evidence.get("focusIndicator")
    )
    findings.append({
        "constraint": "FOCUS_USABLE",
        "owner": "COMPONENT",
        "status": "PASS" if passed else "FAIL",
        "requires_layers": ["geometry", "accessibility", "paint"],
        "evidence_bundle": evidence,
    })
    return findings
