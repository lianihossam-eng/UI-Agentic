# Visual Regression

Visual regression in UI-Agentic combines structural and rendered evidence rather than relying on a single screenshot score.

## Two complementary views

```text
GEOMETRIC REGRESSION
+
PAINT / RASTER / VISUAL REGRESSION
```

### Geometric regression

Explains structural drift:

- what moved;
- where it moved;
- how dimensions changed;
- how spacing/alignment changed;
- whether topology/layering changed;
- whether the change violates a declared contract.

### Paint / visual regression

Captures appearance not represented by geometry alone:

- color;
- typography rasterization;
- images;
- borders/shadows;
- opacity/masks;
- pixel-level fidelity;
- subjective design intent through explicit visual review.

## Evidence identity

Exact screenshot bytes belong to the current-run evidence bundle. Review reuse, when allowed, must use an explicitly versioned deterministic review-identity mechanism and remain bound to the declared visual contract.

## Rule

A visual difference is not automatically a defect. It is a regression only when it violates a declared rule, contract, reference, or accepted visual criterion.
