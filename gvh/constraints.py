"""Constraints — 0 triche: BOUNDED seulement si enclosure prouvée, sinon OBSERVED."""


def gap(a, b, axis="x"):
    return (b[0] - (a[0] + a[2])) if axis == "x" else (b[1] - (a[1] + a[3]))


def check_hard(ir):
    findings = []
    nodes = ir["nodes"]
    cards = [v for v in nodes.values() if v.get("testid") == "card"]
    vw = ir["viewport"]["width"]

    # Fail closed on applicability. An empty violation set is meaningful only
    # when at least one adjacent-card gap was actually measurable.
    if len(cards) < 2:
        findings.append(
            {
                "constraint": "group.uniform_gap",
                "owner": "PAGE",
                "status": "UNKNOWN",
                "reason": "fewer-than-two-applicable-cards",
                "measured_cards": len(cards),
                "viewport": vw,
            }
        )
    else:
        for i in range(len(cards) - 1):
            a = cards[i]["box"]
            b = cards[i + 1]["box"]
            same_row = abs(a[1] - b[1]) < 5
            g = gap(a, b, "x" if same_row else "y")
            axis = "x" if same_row else "y"
            r = abs(g - 24)
            if r > 0.5:
                findings.append(
                    {
                        "constraint": "group.uniform_gap",
                        "owner": "PAGE",
                        "expected": 24,
                        "actual": g,
                        "residual": r,
                        "stability_margin": 0.5 - r,
                        "axis": axis,
                        "viewport": vw,
                        "status": "FAIL",
                    }
                )
                break

    main = next((v for v in nodes.values() if v.get("testid") == "main"), None)
    if main:
        for v in cards:
            if v["box"][0] + v["box"][2] > main["box"][0] + main["box"][2] + 1:
                findings.append(
                    {
                        "constraint": "containment",
                        "owner": "PAGE",
                        "status": "FAIL",
                        "actual": v["box"],
                        "expected": main["box"],
                        "viewport": vw,
                    }
                )
    return findings


def interval_enclosure_honest(sampler, domain, expected, tol):
    """Sans preuve d'enclosure entre samples, downgrade à OBSERVED.

    On retourne OBSERVED avec samples, pas BOUNDED. Un checker BOUNDED doit
    donc refuser cette preuve.
    """
    lo, hi = domain
    samples = {w: sampler(w) for w in range(lo, hi + 1, 32)}
    if hi not in samples:
        samples[hi] = sampler(hi)
    residuals = [abs(v - expected) for v in samples.values()]
    worst = max(residuals)
    worst_w = max(samples, key=lambda w: abs(samples[w] - expected))
    level = "observed"
    status = "PASS" if worst <= tol else "FAIL"
    return {
        "proof_level": level,
        "proof_source": "execution",
        "bound": worst,
        "domain": domain,
        "worst_w": worst_w,
        "samples": len(samples),
        "status": status,
        "note": "sampling only = OBSERVED; BOUNDED requires enclosure proof",
    }
