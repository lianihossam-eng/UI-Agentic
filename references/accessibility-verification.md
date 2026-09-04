# Accessibility and Semantic Verification

Accessibility verification is a distinct UI-Agentic layer. It must not be inferred from geometry or visual appearance alone.

## Verify when applicable

- semantic roles;
- accessible names and descriptions;
- state semantics (`aria-expanded`, `aria-selected`, modal state, etc.);
- reading order;
- keyboard focus order;
- focus containment and return for overlays;
- disabled/hidden semantics;
- reduced-motion behavior when declared;
- compatibility between responsive visual order and semantic/focus order.

## Evidence

Depending on the rule, evidence can include:

- DOM/semantic inspection;
- browser accessibility information where available;
- keyboard traversal;
- focus observations;
- rendered visibility/occlusion evidence for composite focus rules.

## Cross-layer rules

Accessibility results may participate in composite invariants such as `FOCUS_USABLE`, `MODAL_INTEGRITY`, and `VISUAL_SEMANTIC_ORDER`.

A semantic `PASS` does not prove that the element is visible, unobscured, or operable. Those properties require their corresponding geometry/paint/interaction evidence.

## Compliance claims

Do not claim complete WCAG, ACT, or other standards conformance unless the Supported Domain declares the exact standard/version/level/scope and every applicable requirement is closed with appropriate evidence.
