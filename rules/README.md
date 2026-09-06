# Verification Rules

This directory contains the public rule definitions used by UI-Agentic's verification model.

A rule is not a prose preference. It is a named verification obligation with a declared owner, layer, scope, evidence requirement, and pass condition.

---

## Why rules are explicit

Without explicit rules, an automated verifier can easily drift into one of two failure modes:

```text
vague expectation
→ inconsistent checker behavior
```

or:

```text
checker implementation
→ undocumented claim about what it proves
```

UI-Agentic keeps the rule contract visible so the relationship can instead be traced:

```text
requirement / failure mode
        ↕
verification rule
        ↕
compiled scenario obligation
        ↕
evidence / checker result
```

This traceability is part of final confirmation.

---

## Minimal rule model

Architecturally, a rule can declare fields such as:

```yaml
id: unique-rule-id
layer: geometry | paint | interaction | accessibility | temporal
level: page
owner: PAGE
detect: rendered
required_proof: observed | bounded | certified
proof_source: execution | model | hybrid
severity: high
scope: ...
requires: [...]
pass_condition: ...
assumptions: [...]
test_cases: [...]
```

Standards-related rules may additionally require:

```yaml
standards_refs: [...]
applicability: ...
verification_mode: automated | semi-automated | manual | rubric
```

The exact executable representation may be narrower than this target schema. See `../docs/05-project-status-and-roadmap.md` for current implementation boundaries.

---

## Rule ownership

Every rule should have one primary architectural owner:

```text
GLOBAL
FAMILY
PAGE
SECTION
COMPONENT
STATE
DETAIL
```

The owner identifies where a root-cause fix belongs.

For example, a page-level grid problem should not be permanently repaired by adding arbitrary component-level spacing overrides if the page layout owns the relationship.

---

## Rule layers

Rules belong primarily to one verification layer:

- **geometry** — layout, containment, spacing, clipping, responsive structure, layering;
- **paint** — rendered color, contrast, typography, borders, shadows, raster properties;
- **interaction** — hit testing, pointer/touch, keyboard, focus, transitions;
- **accessibility** — roles, names, semantic state, reading/focus order;
- **temporal** — readiness, async behavior, assets/fonts, animation, environment, stability.

A rule may require evidence from several layers. In that case it is a **cross-layer invariant**, but it still has one primary ID and owner rather than becoming several unrelated findings.

---

## Proof requirements

Rules must not silently upgrade evidence strength.

```text
OBSERVED
  direct evidence for a concrete case

BOUNDED
  demonstrated bound over a declared domain region

CERTIFIED
  domain property demonstrated by an applicable method
  and independently checked
```

Ten observations remain observations. They do not automatically satisfy a rule requiring `BOUNDED` or `CERTIFIED` proof.

---

## Verdicts

A rule produces one of three runtime outcomes:

```text
PASS     valid positive evidence
FAIL     valid negative evidence
UNKNOWN  valid verdict cannot be established
```

A missing checker result, ambiguous result, stale proof artifact, failed measurement-readiness condition, or unavailable required instrumentation should become `UNKNOWN` rather than a synthetic pass.

---

## Current example rules

The files in this directory currently demonstrate several rule classes:

- [`global-spacing.md`](global-spacing.md) — product-wide spacing consistency;
- [`page-orders-grid-gap.md`](page-orders-grid-gap.md) — page-level group spacing;
- [`component-button-hit.md`](component-button-hit.md) — interactive target behavior;
- [`accessibility-focus-order.md`](accessibility-focus-order.md) — focus-order behavior;
- [`paint-contrast.md`](paint-contrast.md) — rendered contrast-related verification;
- [`temporal-geometry-stable.md`](temporal-geometry-stable.md) — temporal geometry stability.

They are part of the current reference implementation, not a claim that these six documents represent the complete future rule library.

---

## Adding or modifying a rule

A contribution should answer these questions explicitly:

1. What real requirement or failure mode does the rule represent?
2. Which layer owns detection?
3. Which hierarchy level owns the property?
4. What factors of the Supported Domain can affect it?
5. What scenarios should the compiler generate?
6. What evidence is required?
7. What proof level is required?
8. What makes the result `PASS`, `FAIL`, or `UNKNOWN`?
9. What assumptions are being made?
10. How will a fault in this rule/checker be tested?

A new rule should also preserve bidirectional traceability to the corresponding requirement or failure mode.

---

## Mutation discipline

Critical verification behavior should be tested against known faults.

The expected pattern is:

```text
baseline             → PASS
known fault injected → FAIL or UNKNOWN
fault removed        → PASS
```

If a critical mutant survives, the corresponding verification claim is not considered adequate for final confirmation.

---

## Related documentation

- [Project Guide](../docs/00-project-guide.md)
- [Pyramidal Stabilization](../docs/01-pyramidal-stabilization.md)
- [Agent Architecture & Verification](../docs/02-agent-architecture-and-verification.md)
- [Proof, Evidence, and Attestation](../docs/04-proof-evidence-attestation.md)
- [Supported Domain reference](../references/supported-domain.md)
