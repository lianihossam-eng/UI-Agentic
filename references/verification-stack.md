# Verification Stack

UI-Agentic separates verification into five layers so one class of success cannot hide another class of failure.

| Layer | Responsibility |
| --- | --- |
| Geometry | position, dimensions, spacing, containment, clipping, responsive behavior, layering, occlusion |
| Paint | typography render, color, contrast, borders, shadows, opacity, raster fidelity |
| Interaction | hit testing, pointer/touch, keyboard, focus, scrolling, state transitions |
| Accessibility / Semantics | roles, names, reading order, focus order, ARIA/state semantics, reduced motion |
| Temporal / Environmental | fonts, assets, hydration, async state, animation, runtime/environment stability |

## Cross-layer invariants

Some user-facing properties require an atomic bundle from more than one layer.

Examples:

```text
FOCUS_USABLE
TARGET_OPERABLE
MODAL_INTEGRITY
VISUAL_SEMANTIC_ORDER
ASYNC_STABILITY
```

A layer-specific `PASS` never compensates for failure of a required composite invariant.

## Routing rule

The orchestrator should execute only the layers applicable to the compiled scenario and declared contract. Geometry-specific measurement is delegated to GVH; the other layers remain independent verification concerns.
