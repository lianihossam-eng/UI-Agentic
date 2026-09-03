"""Scenario Compiler — dependency-scoped obligations for the executable domain."""

# In the declared responsive domain every rendered rule can be affected by a
# media query, geometry or occlusion change. Until independence is formally
# demonstrated, viewport_width is therefore a dependency for every UI rule
# below, including state transitions.
RULE_SPECS = {
    "group.uniform_gap": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "global.spacing.scale": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "paint.contrast.text": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "component.button.hit-target": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "TARGET_OPERABLE": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "accessibility.focus-order": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "FOCUS_USABLE": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
    "temporal.geometry-stable": {"factors": ["route", "viewport_width"], "proof_level": "observed"},
}

PROOF_LEVELS = {"observed", "bounded", "certified"}


def scenario_id(scenario):
    """Return a stable unique identity for one compiled proof obligation."""
    route = scenario.get("route", "global")
    viewport = scenario.get("viewport", 768)
    rule = scenario["rule"]
    transition = scenario.get("transition")
    if transition:
        event = transition.get("event", "event")
        source = transition.get("from", "unknown")
        target = transition.get("to", "unknown")
        return f"{route}@{viewport}:{rule}:{event}:{source}->{target}"
    state = scenario.get("state", "default")
    model = scenario.get("model")
    suffix = f":{model}" if model else ""
    return f"{route}@{viewport}:{state}:{rule}{suffix}"


def _finalize(scenario, proof_level="observed"):
    if proof_level not in PROOF_LEVELS:
        raise ValueError(f"unsupported proof level: {proof_level}")
    scenario = dict(scenario)
    scenario["required_proof_level"] = proof_level
    scenario["scenario_id"] = scenario_id(scenario)
    return scenario


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
            scenarios.append(_finalize(scenario, spec.get("proof_level", "observed")))
    return scenarios


def compile(domain):
    scenarios = []
    widths = domain.get("viewport_widths", [768])

    for rule_id, spec in RULE_SPECS.items():
        scenarios.extend(_expand_rule(rule_id, spec, domain))

    for model in domain.get("state_transition_models", []):
        route = model.get("route")

        # Transition semantics are viewport-dependent until independence is
        # formally demonstrated. Execute the full ordered transition sequence
        # at every declared discrete viewport.
        for width in widths:
            for transition in model.get("transitions", []):
                scenarios.append(
                    _finalize(
                        {
                            "rule": f"transition:{model['id']}",
                            "model": model["id"],
                            "route": route,
                            "viewport": width,
                            "transition": transition,
                        }
                    )
                )

        # Modal geometry/interaction/accessibility is likewise observed at
        # every declared discrete viewport.
        if "MODAL_INTEGRITY" in model.get("invariants", []):
            for width in widths:
                scenarios.append(
                    _finalize(
                        {
                            "rule": "MODAL_INTEGRITY",
                            "model": model["id"],
                            "route": route,
                            "viewport": width,
                            "state": "modal-open",
                        }
                    )
                )

    ids = [scenario["scenario_id"] for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario compiler produced duplicate scenario_id values")
    return scenarios
