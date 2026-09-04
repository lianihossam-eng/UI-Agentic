# 02 — UI Agent Architecture & Verification

This document defines the orchestration and verification architecture of UI-Agentic.

It covers modes, progressive disclosure, Supported Domain compilation, verification layers, proof requirements, findings, regression, evidence reuse, visual acceptance, and final confirmation. The stabilization method is defined in [01 — Pyramidal UI Stabilization System](01-pyramidal-stabilization.md). Geometry-specific measurement is defined in [03 — Geometric Visual Harness](03-geometric-visual-harness.md).

---

## 1. Positioning

UI-Agentic is a **stateful orchestrator built around contracts and evidence**.

It is not intended to be a single large design prompt. The orchestrator should know:

- the current operating mode;
- the current hierarchy level and stabilization state;
- the declared Supported Domain;
- which rules apply to the current scope;
- which proof level each rule requires;
- which verification layer owns each measurement;
- which evidence remains valid after a change;
- which findings are open;
- which gates block progression.

The top-level `SKILL.md` acts as a router. It should load only the references and rules needed for the current task.

---

## 2. Canonical operating modes

```text
DISCOVER
DIRECTION
BUILD
AUDIT
VERIFY
REGRESSION
POLISH
```

### DISCOVER

Map the product, existing design system, page families, states, transitions, and supported environment.

### DIRECTION

Propose a global design direction only when one is missing. A proposed direction becomes a parent contract only after it is accepted and recorded.

### BUILD

Implement under the current parent contracts and ownership boundaries.

### AUDIT

Observe, measure, and classify. Audit mode must not silently redefine the visual direction of an existing product.

### VERIFY

Compile applicable obligations, execute the required checks, and produce evidence.

### REGRESSION

Revalidate obligations invalidated by a parent, code, environment, rule, or contract change.

### POLISH

Refine aesthetics only after structural and hard verification gates are sufficiently stable.

---

## 3. Progressive disclosure

The architecture is intentionally split into small public surfaces:

```text
UI-Agentic/
├── SKILL.md
├── docs/
├── references/
├── rules/
├── core/
├── gvh/
├── scripts/
├── evaluations/
└── assets/
```

The expected loading rule is:

```text
mode + hierarchy level + signal + verification layer
→ load the smallest applicable contract/ruleset
```

Do not load the full rules library for every task.

---

## 4. Design contract

### Existing product

For an existing interface:

1. inspect the actual code, tokens, components, and rendered surfaces;
2. extract the real design language;
3. identify inconsistencies explicitly;
4. document the existing system before proposing changes;
5. do not restyle the product merely to make the documentation internally consistent.

### Greenfield product

For a new interface:

```text
propose direction
→ review/accept
→ compile into contract
→ use as parent constraint
```

The contract should capture intent, typography, geometry, spacing, color, shape, elevation, motion, and responsive principles at the appropriate level.

---

## 5. Supported Domain contract

A final confirmation claim is meaningful only if the support boundary is explicit.

A Supported Domain can include:

```yaml
supported_domain:
  routes: []
  viewport_widths: []
  viewport_height: 0
  containers: []
  content_extremes: []
  states: []
  state_transition_models: []
  input_modalities: []
  locales_directions: []
  browsers_platforms: []
  zoom_dpr: []
  temporal_async_scenarios: []
  opaque_surface_adapters: []
  compliance_profiles: []
```

The domain may be intentionally narrow. It may not be narrow **implicitly**.

---

## 6. Scenario Compiler

The Scenario Compiler converts the Supported Domain into the Required Scenario Set.

It should:

1. extract factors from the Supported Domain;
2. map each rule to the factors it actually depends on;
3. partition relevant values into meaningful classes and boundaries;
4. compile exhaustive obligations over each rule's dependency subspace;
5. compose subsystems with `assume → guarantee` contracts when independence is demonstrated;
6. compile required transitions, forbidden transitions, guards, round trips, and temporal properties from declared state models;
7. compile content boundaries/classes deterministically for proof obligations;
8. use additional generated/property-based cases for discovery;
9. use t-way or covering-array exploration only as robustness discovery when appropriate.

### Important distinction

A covering array or large sample set can improve bug discovery. It does not automatically certify an infinite or continuous domain.

Any required obligation that is not executed or otherwise proven remains uncovered or `UNKNOWN`.

---

## 7. Five verification layers

| Layer | Responsibility | Typical evidence |
| --- | --- | --- |
| geometry | position, dimensions, groups, clipping, occlusion, responsive behavior, spatial stability | DOM geometry, Geometry IR, GVH |
| paint | rendered typography, color, contrast, borders, shadows, opacity, raster fidelity | computed styles, screenshots, pixel/perceptual diagnostics |
| interaction | hit testing, pointer/touch, keyboard, focus, scrolling, transitions | browser actions, event/state observations |
| accessibility | roles, names, reading order, focus order, state semantics, reduced motion | semantic inspection, keyboard traversal, accessibility tree where supported |
| temporal | animation, async state, hydration, fonts/images, virtualization, environment | time-series observations, runtime/environment manifest |

The verification engines remain separate so a success in one layer cannot compensate for a failure in another.

---

## 8. Cross-layer contract mesh

Real UI properties often span multiple layers.

A composite invariant should still have:

- one rule ID;
- one primary owner;
- one primary layer;
- an explicit list of required secondary layers;
- one atomic evidence bundle.

Examples:

### `FOCUS_USABLE`

Requires semantic/keyboard correctness, visible/non-obscured geometry, and a perceptible visual focus indicator.

### `TARGET_OPERABLE`

Requires adequate target geometry, correct hit-testing, and absence of critical occlusion.

### `MODAL_INTEGRITY`

Requires valid overlay geometry/layering, focus containment and return, non-operable background content, and correct state behavior.

### `VISUAL_SEMANTIC_ORDER`

Requires responsive visual transformations to remain compatible with declared reading/focus order.

### `ASYNC_STABILITY`

Requires the async transition to complete correctly, final content to remain visible/operable, and forbidden geometric instability to be absent.

A single layer `PASS` never overrides failure of a composite invariant.

---

## 9. Evidence types and proof levels

### Evidence type

A rule can use one or more evidence classes:

- `static` — source, AST, configuration, tokens, files;
- `rendered` — browser, DOM, computed style, Geometry IR, screenshot, hit test;
- `rubric` — explicit qualitative review against a contract or reference.

### Required proof level

A rule separately declares:

```text
observed | bounded | certified
```

When relevant it may also declare:

```text
execution | model | hybrid
```

A model-based result is not automatically proof of real-browser behavior. Its conformance assumptions must be explicit and validated where required.

---

## 10. Trusted Verification Kernel

Evidence producers are not automatically trusted.

The final trust boundary should be as small as practical:

```text
contract
+ evidence or certificate
+ deterministic checker
+ explicit assumptions
```

For strong certification claims, the checker should validate the witness rather than reproduce the entire reasoning process of the generator.

If a required certificate cannot be independently validated, the result is `UNKNOWN`.

---

## 11. Minimum rule schema

A public rule should be understandable without reading verifier internals.

Example:

```yaml
id: page.orders.grid-gap
layer: geometry
level: page
owner: PAGE
detect: rendered
required_proof: observed
proof_source: execution
severity: high
scope: orders-grid
requires: []
pass_condition: gap matches the declared page contract within tolerance
assumptions: []
test_cases: []
```

Rules associated with a normative standard should additionally declare version, scope, applicability, and the relation between the rule and the normative requirement.

---

## 12. Findings and Diagnosis Gate

A finding must contain enough information to reproduce and own the problem.

Minimum useful shape:

```yaml
id: unique-rule-id
layer: geometry | paint | interaction | accessibility | temporal
owner: GLOBAL | FAMILY | PAGE | SECTION | COMPONENT | STATE | DETAIL
evidence: ...
proof_level: observed | bounded | certified
expected: ...
actual: ...
status: FAIL | UNKNOWN
```

Before patching a group of correlated findings:

```text
failing findings
→ dependency slice
→ smallest reproducible failing case
→ minimal or near-minimal conflict set where applicable
→ candidate root cause
→ valid owner
→ targeted fix
```

Useful mechanisms include:

- dependency slicing;
- delta debugging;
- constraint conflict-core reduction;
- ownership inference.

The objective is to fix one root cause instead of applying multiple symptom-level patches.

---

## 13. Same-rule revalidation

Every fix must close the loop that produced it:

```text
finding
→ fix
→ rerun SAME triggering rule
→ PASS?
   ├─ yes → close + targeted regression
   └─ no  → continue, revert, or escalate
```

A fix that has not revalidated its triggering rule remains open.

---

## 14. Evidence DAG

Evidence is content-addressed and dependency-aware.

A canonical evidence identity can include:

```text
code / subject identity
contract
rule
scenario
browser/build
platform
fonts/assets
locale/DPR
verifier/checker identity
```

Evidence can be reused only if the declared dependencies remain compatible.

When a parent or input changes, affected evidence becomes stale. Unaffected evidence may remain valid.

This is the basis of dependency-aware regression.

---

## 15. Measurement Readiness Gate

Rendered evidence must not be collected from an arbitrary intermediate frame.

The readiness gate can require:

- deterministic data/network fixtures;
- controlled time/timezone/randomness where relevant;
- expected application state;
- fonts resolved;
- expected asset state;
- hydration complete;
- async work settled according to the contract;
- geometry stable for the declared window;
- animations controlled or explicitly under test.

A timeout alone is not proof of readiness.

Readiness failure produces `UNKNOWN` for required rendered obligations.

---

## 16. Paint verification ladder

Paint verification should distinguish different strengths of evidence:

```text
P0 — STYLE CONTRACT
     resolved styles, token/source lineage, font/asset identity

P1 — NORMATIVE VISUAL RULES
     contrast/color/appearance equations when defined by a contract or standard

P2 — HERMETIC RASTER FIDELITY
     exact or thresholded pixel comparison under controlled renderer inputs

P3 — PERCEPTUAL DIAGNOSTICS
     SSIM, perceptual color difference, regional metrics for diagnosis/prioritization

P4 — VISUAL ACCEPTANCE
     rubric/reference-based review of visual intent
```

Perceptual metrics are diagnostics unless the contract explicitly validates their use as a pass/fail criterion.

---

## 17. Coverage Ledger

Coverage is a closure mechanism, not an aesthetic score.

A ledger can track:

| Dimension | Required | Tested | Pass | Fail | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| routes/surfaces | n | n | n | 0 | 0 |
| states | n | n | n | 0 | 0 |
| responsive/container obligations | n | n | n | 0 | 0 |
| interaction paths | n | n | n | 0 | 0 |
| accessibility obligations | n | n | n | 0 | 0 |
| temporal/environmental obligations | n | n | n | 0 | 0 |

`100%` means all **required** obligations are closed at the required proof level.

---

## 18. Rule Adequacy Gate

Perfect execution of an incomplete ruleset is not enough.

Traceability should connect:

```text
requirement / failure mode
↔ verification rule
↔ scenario/domain obligation
↔ evidence or certificate
```

Mutation/fault-injection tests are used to challenge the verifier. A critical mutant that survives means the verification rules or checkers are not yet adequate for the claimed failure mode.

---

## 19. Visual Acceptance Contract

The final visual review should be explicit rather than hidden in reviewer intuition.

The contract may define:

- hierarchy;
- composition;
- perceived typography;
- density/whitespace;
- coherence;
- brand/imagery;
- anchors or exemplars;
- disqualifying defects;
- reviewer identity and scope;
- adjudication rules for ambiguous critical criteria.

Output:

```text
ACCEPTED | REJECTED | UNKNOWN
```

Visual acceptance remains subjective rubric evidence. It is never `CERTIFIED`.

---

## 20. Final Confirmation Gate

Final confirmation requires simultaneous closure of the relevant gates, including:

```text
coverage
requirement/failure-mode traceability
required proof levels
certificate/checker validation
measurement readiness
mutation adequacy
explicit assumptions
regression closure
parent contract validity
state/transition coverage
cross-layer invariants
compliance obligations where declared
critical geometry/paint failures
critical temporal/environmental instability
visual acceptance
```

Any required missing gate is a blocker.

---

## 21. Attestation

A `LOCKED` result is a content-bound attestation over an identified snapshot.

It should bind, as applicable:

- subject/build identity;
- contract digest;
- scenario digest;
- rule/checker digest;
- measurement kernel digest;
- trusted verification kernel digest;
- environment manifest digest;
- runtime identity;
- Evidence DAG root;
- report root;
- visual evidence root;
- final gate.

Any material input change makes the affected proof stale and requires controlled revalidation.

For the full model, see [04 — Proof, Evidence, and Attestation](04-proof-evidence-attestation.md).
