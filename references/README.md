# Operational References

This directory contains **focused implementation references** used by UI-Agentic during stabilization, verification, and review.

These files are intentionally narrower than the architecture documents in `docs/`.

Use them when you already understand the overall project and need operational guidance for one verification concern.

---

## How references fit into the project

```text
README / Project Guide
        ↓
Core specifications in docs/
        ↓
Operational references here
        ↓
Rules / verifier implementation
```

The core specifications define the architecture. References explain how a specific concern should be applied in practice. They must not silently redefine the architecture.

If a reference conflicts with an executable rule or a current normative contract for a specific commit, inspect the current implementation and status documentation rather than assuming the reference overrides it.

---

## Reference index

### [Global Design Contract](global-design-contract.md)

How shared product-wide design decisions are captured and treated as parent constraints.

Use this when establishing or extracting typography, spacing, semantic color, shape, elevation, motion, and responsive philosophy.

### [Supported Domain](supported-domain.md)

How to declare the product surface covered by a verification claim.

Use this when defining routes, viewports, states, inputs, locales, environments, content extremes, temporal conditions, and other support dimensions.

### [Verification Stack](verification-stack.md)

A focused overview of the five verification layers and their separation.

Use this when deciding which layer owns a rule and which evidence source is appropriate.

### [Paint Verification](paint-verification.md)

Operational guidance for rendered paint checks such as style identity, color/contrast, raster comparison, and visual diagnostics.

### [Interaction Verification](interaction-verification.md)

Operational guidance for hit testing, keyboard/pointer behavior, focus, scrolling, and transitions.

### [Accessibility Verification](accessibility-verification.md)

Operational guidance for semantics, roles, accessible names, focus/reading order, keyboard traversal, and standards-related claims.

This reference does not itself establish complete accessibility conformance.

### [Temporal and Environmental Verification](temporal-environmental-verification.md)

Operational guidance for readiness, hydration, async state, assets/fonts, animation, layout stability, and environment identity.

### [Visual Regression](visual-regression.md)

How to reason about rendered change using geometric, raster, and subjective visual evidence without collapsing them into one score.

### [Anti-Drift](anti-drift.md)

Rules for preventing lower-level exceptions from gradually redefining stabilized parent contracts.

### [Ship Readiness](ship-readiness.md)

A concise closure checklist for verification and release-readiness decisions.

---

## Which document should I read?

```text
Need overall architecture?
→ ../docs/00-project-guide.md

Need hierarchy / ownership?
→ ../docs/01-pyramidal-stabilization.md

Need Scenario Compiler / evidence / gates?
→ ../docs/02-agent-architecture-and-verification.md

Need geometry theory?
→ ../docs/03-geometric-visual-harness.md

Need proof / attestation model?
→ ../docs/04-proof-evidence-attestation.md

Need current implementation boundary?
→ ../docs/05-project-status-and-roadmap.md

Need one operational concern?
→ use the focused references in this directory
```

---

## Reference-writing rule

A public operational reference should always state:

1. **what problem it addresses**;
2. **which verification layer or ownership level it belongs to**;
3. **what evidence it expects**;
4. **what it can and cannot prove**;
5. **which higher-level specification governs it**.

References should remain short enough to load selectively during agent execution and specific enough that two readers interpret the operational requirement in the same way.
