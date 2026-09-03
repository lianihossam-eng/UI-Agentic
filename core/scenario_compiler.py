"""Scenario Compiler — dependency-scoped obligations for the executable domain."""

# In the declared responsive domain every rendered rule can be affected by a
# media query, geometry or occlusion change. Until independence is formally
# demonstrated, viewport_width is therefore a dependency for every static UI
# rule below.
RULE_SPECS = {
    "group.uniform_gap": {"factors": ["route", "viewport_width"]},
    "global.spacing.scale": {"factors": ["route", "viewport_width"]},
    "paint.contrast.text": {"factors": ["route", "viewport_width"]},
    "component.button.hit-target": {"factors": ["route", "viewport_width"]},
    "TARGET_OPERABLE": {"factors": ["route", "viewport_width"]},
    "accessibility.focus-order": {"factors": ["route", "viewport_width"]},
    "FOCUS_USABLE": {"factors": ["route", "viewport_width"]},
    "temporal.geometry-stable": {"factors": ["route", "viewport_width"]},
}


def _expand_rule(rule_id, spec, domain):
    factors = spec.get("factors", [])
    routes = domain.get("routes", []) if "route" in factors else [None]
    widths = domain.get("viewport_widths", [768]) if "viewport_width" in factors else [768]
    scenarios = []
    for route in routes:
        for width in widths:
            scenario = {"rule": rule_id, "viewport": width}
            if route is not None:
                scenario["route"] = route
            scenarios.append(scenario)
    return scenarios


def compile(domain):
    scenarios = []
    widths = domain.get("viewport_widths", [768])

    for rule_id, spec in RULE_SPECS.items():
        scenarios.extend(_expand_rule(rule_id, spec, domain))

    for model in domain.get("state_transition_models", []):
        route = model.get("route")

        # Transition event semantics are currently executed at the canonical
        # 768px interaction viewport. They remain a distinct dependency class
        # from rendered state invariants; no claim of viewport-exhaustive
        # transition execution is made here.
        for transition in model.get("transitions", []):
            scenarios.append(
                {
                    "rule": f"transition:{model['id']}",
                    "model": model["id"],
                    "route": route,
                    "viewport": 768,
                    "transition": transition,
                }
            )

        # Modal geometry/interaction/accessibility is viewport-dependent and
        # must be observed at every declared discrete viewport.
        if "MODAL_INTEGRITY" in model.get("invariants", []):
            for width in widths:
                scenarios.append(
                    {
                        "rule": "MODAL_INTEGRITY",
                        "model": model["id"],
                        "route": route,
                        "viewport": width,
                        "state": "modal-open",
                    }
                )
    return scenarios
