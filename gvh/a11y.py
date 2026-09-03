"""Accessibility checks — real keyboard order + cross-layer focus evidence."""

FOCUSABLE_SELECTOR = (
    'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), '
    'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
)


def check_a11y(page, ir):
    focusables = page.evaluate(
        f"""() => [...document.querySelectorAll('{FOCUSABLE_SELECTOR}')].filter(e => {{
          const s=getComputedStyle(e); const r=e.getBoundingClientRect();
          return !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
        }}).map((e,index) => ({{
          index,
          key:`${{e.dataset.testid || e.tagName.toLowerCase()}}#${{index}}`
        }}))"""
    )

    # blur() does not reset Chromium's sequential-focus navigation starting
    # point. Anchor focus explicitly on BODY with tabindex=-1, which is
    # programmatically focusable but excluded from sequential Tab order and is
    # positioned before all descendants. This gives a deterministic real-key
    # traversal without adding a sequential focus target.
    body_tabindex = page.evaluate(
        """() => {
          const body=document.body;
          const had=body.hasAttribute('tabindex');
          const old=body.getAttribute('tabindex');
          body.setAttribute('tabindex','-1');
          body.focus();
          return {had, old, focused:document.activeElement===body};
        }"""
    )

    actual_indices = []
    if body_tabindex.get("focused"):
        for _ in range(len(focusables)):
            page.keyboard.press("Tab")
            active_index = page.evaluate(
                f"""() => {{
                  const list=[...document.querySelectorAll('{FOCUSABLE_SELECTOR}')].filter(e => {{
                    const s=getComputedStyle(e); const r=e.getBoundingClientRect();
                    return !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
                  }});
                  return list.indexOf(document.activeElement);
                }}"""
            )
            actual_indices.append(active_index)

    page.evaluate(
        """saved => {
          const body=document.body;
          if(saved.had) body.setAttribute('tabindex', saved.old ?? '');
          else body.removeAttribute('tabindex');
        }""",
        body_tabindex,
    )

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
    elif not body_tabindex.get("focused"):
        findings.append(
            {
                "constraint": "accessibility.focus-order",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "cannot-establish-keyboard-traversal-anchor",
                "focusable_keys": [item["key"] for item in focusables],
                "measured_count": len(focusables),
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
                "traversal_anchor": "body[tabindex=-1]",
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
        applicable = button.evaluate(
            """e => {
              const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
              return !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
            }"""
        )
        if not applicable:
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
                visible: !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0,
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
                "reason": "no-visible-non-inert-button",
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
