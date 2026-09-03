"""Accessibility checks — real keyboard order + cross-layer focus evidence."""

FOCUSABLE_SELECTOR = (
    'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), '
    'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
)


def check_a11y(page, ir):
    focusables = page.evaluate(
        f"""() => [...document.querySelectorAll('{FOCUSABLE_SELECTOR}')].filter(e => {{
          const s=getComputedStyle(e); const r=e.getBoundingClientRect();
          return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
        }}).map((e,index) => ({{
          index,
          key:`${{e.dataset.testid || e.tagName.toLowerCase()}}#${{index}}`
        }}))"""
    )

    page.evaluate("() => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); }")
    actual_indices = []
    for _ in range(len(focusables)):
        page.keyboard.press("Tab")
        active_index = page.evaluate(
            f"""() => {{
              const list=[...document.querySelectorAll('{FOCUSABLE_SELECTOR}')].filter(e => {{
                const s=getComputedStyle(e); const r=e.getBoundingClientRect();
                return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
              }});
              return list.indexOf(document.activeElement);
            }}"""
        )
        actual_indices.append(active_index)

    findings = []
    if not focusables:
        findings.append(
            {
                "constraint": "accessibility.focus-order",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "no-focusable-elements",
            }
        )
    else:
        expected_indices = list(range(len(focusables)))
        findings.append(
            {
                "constraint": "accessibility.focus-order",
                "owner": "PAGE",
                "status": "PASS" if actual_indices == expected_indices else "FAIL",
                "expected_indices": expected_indices,
                "actual_indices": actual_indices,
                "focusable_keys": [item["key"] for item in focusables],
                "measured_count": len(focusables),
            }
        )

    buttons = page.locator("button:not([disabled])")
    button_count = buttons.count()
    if button_count == 0:
        findings.append(
            {
                "constraint": "FOCUS_USABLE",
                "owner": "COMPONENT",
                "status": "UNKNOWN",
                "reason": "no-button",
                "requires_layers": ["geometry", "accessibility", "paint"],
            }
        )
        return findings

    evidence_items = []
    for index in range(button_count):
        button = buttons.nth(index)
        visible = button.evaluate(
            """e => {
              const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
              return s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
            }"""
        )
        if not visible:
            continue
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
                boxShadow:s.boxShadow,
                testid:e.dataset.testid || null
              };
            }"""
        )
        evidence["index"] = index
        evidence["passed"] = bool(
            evidence.get("focused")
            and evidence.get("visible")
            and evidence.get("notObscured")
            and evidence.get("focusIndicator")
        )
        evidence_items.append(evidence)

    if not evidence_items:
        findings.append(
            {
                "constraint": "FOCUS_USABLE",
                "owner": "COMPONENT",
                "status": "UNKNOWN",
                "reason": "no-visible-button",
                "requires_layers": ["geometry", "accessibility", "paint"],
            }
        )
        return findings

    failures = [item for item in evidence_items if not item["passed"]]
    findings.append(
        {
            "constraint": "FOCUS_USABLE",
            "owner": "COMPONENT",
            "status": "FAIL" if failures else "PASS",
            "requires_layers": ["geometry", "accessibility", "paint"],
            "measured_count": len(evidence_items),
            "failure_count": len(failures),
            "evidence_bundle": evidence_items,
        }
    )
    return findings
