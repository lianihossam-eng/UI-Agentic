"""Accessibility checks — deterministic keyboard order + cross-layer focus evidence."""

# The broad surface intentionally includes tabindex=-1. Visible native controls
# may not disappear from the proof set merely because a mutation removes them
# from sequential keyboard navigation.
KEYBOARD_SURFACE_SELECTOR = (
    'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), '
    'textarea:not([disabled]), [tabindex]'
)
NATIVE_INTERACTIVE_SELECTOR = (
    'button:not([disabled]), a[href], input:not([disabled]), '
    'select:not([disabled]), textarea:not([disabled])'
)


def _active_keyboard_surface(page):
    return page.evaluate(
        f"""() => [...document.querySelectorAll('{KEYBOARD_SURFACE_SELECTOR}')].filter(e => {{
          const s=getComputedStyle(e); const r=e.getBoundingClientRect();
          return !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
        }}).map((e,index) => ({{
          domIndex:index,
          key:`${{e.dataset.testid || e.tagName.toLowerCase()}}#${{index}}`,
          tabIndex:e.tabIndex,
          nativeInteractive:e.matches('{NATIVE_INTERACTIVE_SELECTOR}')
        }}))"""
    )


def check_a11y(page, ir):
    keyboard_surface = _active_keyboard_surface(page)
    findings = []

    if not keyboard_surface:
        findings.append(
            {
                "constraint": "accessibility.focus-order",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "no-active-visible-keyboard-surface",
                "proof_level": "observed",
            }
        )
    else:
        removed_native = [
            item
            for item in keyboard_surface
            if item.get("nativeInteractive") and int(item.get("tabIndex", -1)) < 0
        ]
        positive_tabindex = [
            item for item in keyboard_surface if int(item.get("tabIndex", -1)) > 0
        ]
        sequential = [
            item for item in keyboard_surface if int(item.get("tabIndex", -1)) >= 0
        ]

        actual_indices = []
        keyboard_navigation_ok = bool(sequential)
        first_focus_ok = False
        if sequential:
            # Establish a deterministic real keyboard starting point by focusing
            # the first sequential control itself. Then verify every internal
            # adjacency with actual Tab events. We deliberately do not assert
            # end-of-document wrapping here; modal wrapping/containment belongs
            # to MODAL_INTEGRITY.
            first_focus_ok = bool(
                page.evaluate(
                    f"""() => {{
                      const list=[...document.querySelectorAll('{KEYBOARD_SURFACE_SELECTOR}')].filter(e => {{
                        const s=getComputedStyle(e); const r=e.getBoundingClientRect();
                        return !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0 && e.tabIndex>=0;
                      }});
                      if(!list.length) return false;
                      list[0].focus();
                      return document.activeElement===list[0];
                    }}"""
                )
            )
            keyboard_navigation_ok = first_focus_ok
            for expected_index in range(1, len(sequential)):
                page.keyboard.press("Tab")
                active_index = page.evaluate(
                    f"""() => {{
                      const list=[...document.querySelectorAll('{KEYBOARD_SURFACE_SELECTOR}')].filter(e => {{
                        const s=getComputedStyle(e); const r=e.getBoundingClientRect();
                        return !e.closest('[inert]') && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0 && e.tabIndex>=0;
                      }});
                      return list.indexOf(document.activeElement);
                    }}"""
                )
                actual_indices.append(active_index)
                if active_index != expected_index:
                    keyboard_navigation_ok = False

        expected_indices = list(range(1, len(sequential)))
        passed = (
            bool(sequential)
            and first_focus_ok
            and not removed_native
            and not positive_tabindex
            and keyboard_navigation_ok
            and actual_indices == expected_indices
        )
        findings.append(
            {
                "constraint": "accessibility.focus-order",
                "owner": "PAGE",
                "status": "PASS" if passed else "FAIL",
                "proof_level": "observed",
                "expected_indices": expected_indices,
                "actual_indices": actual_indices,
                "focusable_keys": [item["key"] for item in sequential],
                "keyboard_surface_count": len(keyboard_surface),
                "measured_count": len(sequential),
                "removed_native_controls": removed_native,
                "positive_tabindex_controls": positive_tabindex,
                "first_focus_ok": first_focus_ok,
                "keyboard_navigation_ok": keyboard_navigation_ok,
                "navigation_contract": "DOM-order native controls; no positive tabindex; internal Tab adjacencies",
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
