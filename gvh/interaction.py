"""Interaction verification over all visible instrumented controls."""


def check_interaction(ir):
    buttons = [
        value
        for value in ir["nodes"].values()
        if value.get("visible")
        and (value.get("tag") == "button" or value.get("testid") in ("btn", "close", "open-modal"))
    ]

    if not buttons:
        unknown = {
            "owner": "COMPONENT",
            "status": "UNKNOWN",
            "reason": "no-visible-button",
            "proof_level": "observed",
        }
        return [
            {"layer": "interaction", "constraint": "component.button.hit-target", **unknown},
            {
                "layer": "interaction",
                "constraint": "TARGET_OPERABLE",
                "requires_layers": ["geometry", "interaction"],
                **unknown,
            },
        ]

    measurements = []
    for index, value in enumerate(buttons):
        width, height = value["box"][2], value["box"][3]
        hit_ok = bool(value.get("hit", {}).get("hitOk", False))
        region = value.get("visibleRegion", [0, 0, 0, 0])
        visible_region = len(region) >= 4 and region[2] > 0 and region[3] > 0
        target_ok = width >= 44 and height >= 44 and hit_ok
        operable = target_ok and visible_region
        measurements.append(
            {
                "index": index,
                "testid": value.get("testid"),
                "size": [width, height],
                "hit": hit_ok,
                "visible_region": visible_region,
                "target_ok": target_ok,
                "operable": operable,
            }
        )

    target_failures = [item for item in measurements if not item["target_ok"]]
    operability_failures = [item for item in measurements if not item["operable"]]

    return [
        {
            "layer": "interaction",
            "constraint": "component.button.hit-target",
            "owner": "COMPONENT",
            "status": "FAIL" if target_failures else "PASS",
            "proof_level": "observed",
            "measured_count": len(measurements),
            "failure_count": len(target_failures),
            "failures": target_failures,
            "evidence_bundle": measurements,
        },
        {
            "layer": "interaction",
            "constraint": "TARGET_OPERABLE",
            "owner": "COMPONENT",
            "status": "FAIL" if operability_failures else "PASS",
            "proof_level": "observed",
            "requires_layers": ["geometry", "interaction"],
            "measured_count": len(measurements),
            "failure_count": len(operability_failures),
            "failures": operability_failures,
            "evidence_bundle": measurements,
        },
    ]
