# Project Guide — UI-Agentic from A to Z

This guide explains UI-Agentic as a complete system rather than as a collection of files.

It is written for readers who want to understand:

- what the project is trying to solve;
- how the architecture is organized;
- how a UI moves from discovery to a verified state;
- how browser evidence becomes a trustworthy claim;
- what the Geometric Visual Harness does;
- what `100% confirmed` and `LOCKED` actually mean;
- which parts are implemented today and which remain architectural targets.

For exact normative details, follow the links to the dedicated specifications.

---

## 1. The core idea

UI-Agentic treats interface quality as a **contracted, hierarchical, evidence-producing process**.

Most UI tooling focuses on one layer:

- screenshots;
- accessibility checks;
- CSS linting;
- visual regression;
- browser automation;
- design-system validation.

UI-Agentic does not replace those categories. It coordinates them inside a single model.

The system asks four questions in order:

```text
1. What does this product claim to support?
2. Which design level owns each important constraint?
3. What evidence is required to verify each obligation?
4. Can the final confidence claim be reproduced and independently checked?
```

The project exists because skipping any one of these questions can produce misleading confidence.

---

## 2. The hierarchy: where UI decisions belong

The stabilization hierarchy is:

```text
GLOBAL
  ↓
FAMILY
  ↓
PAGE
  ↓
SECTION
  ↓
COMPONENT
  ↓
STATE
  ↓
DETAIL
```

Each level owns a different class of decisions.

### Global

The product-wide visual language:

- typography scale;
- semantic color system;
- spacing scale;
- radii;
- borders and elevation;
- motion philosophy;
- shared primitives;
- global responsive philosophy.

### Family

Patterns shared by related pages:

- application shell;
- navigation;
- shared headers;
- content containers;
- family-level density;
- common loading/error structure;
- responsive transformation shared by several pages.

### Page

A single page's structural purpose:

- primary user goal;
- primary and secondary actions;
- information hierarchy;
- macro layout;
- page-specific density;
- page states;
- business constraints.

### Section

Relationships between blocks inside a page:

- internal grid;
- toolbar layout;
- section-level ordering;
- block relationships;
- responsive stacking/wrapping behavior.

### Component

The internal contract of a reusable element:

- anatomy;
- variants;
- internal spacing;
- dimensions;
- control sizing;
- local responsive adaptation;
- component states.

### State

Rendered and interactive states:

- default;
- hover;
- focus;
- active;
- selected;
- disabled;
- loading;
- empty;
- error;
- success;
- modal/drawer open;
- short/long content;
- permission and latency variants.

### Detail

Fine polish that must not alter the established structure:

- optical offsets;
- micro-spacing;
- icon weight;
- subtle border/shadow tuning;
- letter spacing;
- motion timing.

The governing invariant is:

> A lower level may not solve its local problem by silently destabilizing a higher-level contract.

That principle is defined in detail in [01 — Pyramidal UI Stabilization System](01-pyramidal-stabilization.md).

---

## 3. Why stabilization is top-down

Suppose a card is too narrow on one screen.

A purely local approach might change the card width.

UI-Agentic instead asks:

```text
Is the problem owned by the component?
        │
        ├─ yes → fix the component
        │
        └─ no
            ↓
Is the section grid wrong?
        │
        ├─ yes → fix the section
        │
        └─ no
            ↓
Is the page macro-layout wrong?
        │
        ├─ yes → fix the page
        │
        └─ no
            ↓
Does the family/global contract need escalation?
```

This avoids a common failure mode: many local patches that individually look reasonable but collectively destroy the design system.

The rule is **lowest valid owner**, not "always local" and not "always global".

---

## 4. Stabilization states

Every meaningful UI scope can move through explicit states:

```text
UNEXPLORED
→ DRAFT
→ STRUCTURED
→ STABLE
→ VERIFIED
→ LOCKED
```

### UNEXPLORED

The surface has not been sufficiently mapped.

### DRAFT

Direction exists, but the structure is still fluid.

### STRUCTURED

The architecture and relationships are defined. Major changes are still acceptable.

### STABLE

The level is coherent enough for work to proceed safely to lower levels.

### VERIFIED

Applicable verification obligations have passed with the required evidence.

### LOCKED

The state is tied to a verification attestation. Future changes require impact analysis and controlled revalidation.

A descendant should not be considered fully verified while a required parent is structurally unstable.

---

## 5. Breadth before depth

UI-Agentic deliberately avoids polishing one page to completion while the rest of the product remains structurally unknown.

Bad sequencing:

```text
Dashboard 100% polished
Orders     unexplored
Settings   unexplored
Analytics  unexplored
```

Preferred sequencing:

```text
Global language established
        ↓
representative families stabilized
        ↓
major page structures stabilized
        ↓
cross-page validation
        ↓
section/component/state completion
        ↓
polish
```

This exposes weak global decisions earlier, when they are cheaper to correct.

---

## 6. The Supported Domain: what the claim actually covers

UI-Agentic does not allow an unbounded statement such as "the UI is correct".

The product must first declare what is supported.

Conceptually:

```text
Dₛ = Routes
   × Viewports
   × Containers
   × Content
   × States
   × Inputs
   × Locales
   × Environments
   × Time
```

A real Supported Domain can include:

- routes and surfaces;
- viewport ranges;
- container sizes;
- UI states;
- transition models;
- content extremes;
- keyboard, mouse, touch, or other inputs;
- locale and text direction;
- browser/platform requirements;
- zoom and DPR;
- asynchronous and temporal scenarios;
- compliance profiles;
- opaque-surface adapters where internal geometry cannot be observed directly.

The domain may be deliberately narrow. What matters is that it is explicit.

A product that supports only Chromium at selected viewport ranges should say exactly that. The correct response is not to pretend multi-browser coverage exists.

---

## 7. The Scenario Compiler

The Supported Domain can be large. UI-Agentic therefore does not blindly execute the entire Cartesian product.

Instead, the Scenario Compiler uses rule dependencies.

Conceptually:

```text
Supported Domain
      ↓
extract factors
      ↓
map each rule to the factors it actually reads
      ↓
partition boundaries/classes where appropriate
      ↓
compile required obligations
      ↓
add transition-path obligations
      ↓
add robustness discovery for unknown interactions
```

A rule that only depends on route and viewport does not need to be multiplied by unrelated locale values unless locale can affect that rule.

However, dependency reduction must be justified. Unknown dependence cannot simply be ignored.

The compiler also handles interaction paths rather than state snapshots alone. A meaningful flow may require:

```text
default
  -- click open --> modal-open
  -- Escape -----> default
```

Both states and transitions matter.

For generative or property-based discovery, random runs can find failures, but they do not automatically certify an infinite domain. Any discovered in-domain failure should be reduced to a minimal reproducible regression case.

The complete architecture is defined in [02 — UI Agent Architecture & Verification](02-agent-architecture-and-verification.md).

---

## 8. The five verification layers

UI-Agentic separates verification into five layers.

### Layer 1 — Geometry

Questions such as:

- Is an element inside its container?
- Are gaps consistent?
- Does the layout overflow?
- Is a modal positioned correctly?
- Is a control clipped?
- Is an overlay painted above the content it is meant to cover?
- Where does a responsive layout change topology?

This is the primary domain of the Geometric Visual Harness.

### Layer 2 — Paint

Questions such as:

- Are rendered colors correct?
- Is contrast acceptable under the declared rule?
- Did a border, shadow, opacity, or mask change?
- Does the raster output match the declared baseline under a controlled renderer?

### Layer 3 — Interaction

Questions such as:

- Does the intended element receive the click?
- Can the user operate the UI with keyboard input?
- Does focus move correctly?
- Does scrolling behave as expected?
- Are state transitions correct?

### Layer 4 — Accessibility and semantics

Questions such as:

- Is the control represented with the correct role?
- Does it have an accessible name?
- Does reading order match the intended structure?
- Does focus order remain coherent after responsive transformation?
- Are state semantics represented correctly?

UI-Agentic does not equate the existence of some accessibility checks with complete standards conformance.

### Layer 5 — Temporal and environmental behavior

Questions such as:

- Were fonts loaded before measurement?
- Did hydration finish?
- Did an asynchronous state stabilize?
- Does late-loading content move the layout unexpectedly?
- Is the browser/runtime/environment identity known?
- Are animations controlled or explicitly included in the test?

A fixed sleep is not proof of readiness.

---

## 9. Cross-layer invariants

Real usability often spans several layers.

Consider a button.

It may have:

```text
correct semantic role       PASS
sufficient geometric size   PASS
```

but still fail because another transparent element intercepts the pointer.

UI-Agentic therefore supports composite invariants.

### TARGET_OPERABLE

Combines geometry and interaction evidence: the target is large enough, visible enough, not critically occluded, and receives the intended hit test.

### FOCUS_USABLE

Combines keyboard/focus semantics with visibility and visual focus indication.

### MODAL_INTEGRITY

Can combine:

- correct overlay/layer behavior;
- visible modal geometry;
- focus containment;
- background non-operability;
- correct close/return behavior;
- temporal/state consistency.

### VISUAL_SEMANTIC_ORDER

Checks that visual reordering remains compatible with declared reading and focus order.

### ASYNC_STABILITY

Checks that asynchronous transitions reach a stable, visible, operable final state without forbidden layout instability.

One layer cannot "outvote" a failure in another.

---

## 10. Measurement Readiness

Rendered evidence is only meaningful after the application reaches a valid observation point.

The Measurement Readiness Gate can check:

```text
expected route/state reached
fonts ready
required assets resolved
hydration complete
async work settled as declared
animations controlled or intentionally active
geometry stable for the declared observation window
locale/time/randomness/environment controlled where relevant
```

If readiness cannot be established, rendered obligations become `UNKNOWN`.

This is a key fail-closed behavior: uncertainty is represented explicitly instead of being converted into a convenient pass.

---

## 11. Geometric Visual Harness (GVH)

The GVH is the objective geometry engine inside UI-Agentic.

The browser remains the real layout simulator. GVH measures the rendered result; it does not attempt to recreate CSS layout independently.

A basic rendered box can be represented as:

```text
Bᵢ = (xᵢ, yᵢ, wᵢ, hᵢ)
```

but modern UI geometry needs more than boxes. The architecture defines a spatial precision ladder:

```text
L0 — layout box
L1 — fragments / client rects
L2 — transformed region
L3 — clipped / visible region
L4 — layered region with paint/occlusion relationships
```

This matters because a box can be geometrically present while still being clipped, transformed, or hidden behind another layer.

The GVH also models group relationships:

```text
EQUAL_WIDTH(cards[*])
UNIFORM_GAP_Y(items[*])
ALIGN_LEFT(group[*])
COLUMN_RATIO(left, right)
```

and layer relationships:

```text
PAINTED_ABOVE(A, B)
OCCLUDES(A, B)
CLIPPED_BY(node, ancestor)
OVERLAY_ABOVE_CONTENT(overlay)
```

See [03 — Geometric Visual Harness](03-geometric-visual-harness.md) for the mathematical model.

---

## 12. Responsive verification

Responsive behavior is not merely a list of screenshots at familiar breakpoints.

The architecture treats layout as a function of the environment:

```text
xᵢ = fᵢ(W)
wᵢ = gᵢ(W)
```

A future-complete responsive analysis can perform:

```text
coarse sweep
   ↓
suspect interval
   ↓
adaptive subdivision
   ↓
boundary search
   ↓
critical width
```

Topology can also change intentionally:

```text
Desktop: sidebar LEFT_OF content
Mobile:  sidebar ABOVE content
```

A declared topology transition is not itself a regression.

The current implementation status of continuous responsive analysis is documented in [05 — Implementation Status and Roadmap](05-project-status-and-roadmap.md).

---

## 13. Findings and ownership

A verification finding should be specific and actionable.

A minimal finding model includes:

```yaml
id: page.orders.grid-gap
layer: geometry
owner: PAGE
expected: 24
actual: 20
proof_level: observed
status: FAIL
```

The key property is `owner`.

Without ownership, automated systems tend to patch the nearest visible symptom. UI-Agentic instead tries to identify the correct architectural level.

---

## 14. Diagnosis before repair

Several failures can share one root cause.

For correlated findings, the intended diagnosis sequence is:

```text
failing findings
      ↓
dependency slice
      ↓
smallest reproducible failure
      ↓
minimal / near-minimal conflict set
      ↓
candidate root cause
      ↓
valid owner
      ↓
targeted fix
```

Possible mechanisms include:

- dependency slicing;
- delta debugging;
- conflict-core extraction for formalized constraints;
- owner inference.

The purpose is simple: avoid creating five local patches for one parent-level defect.

---

## 15. The same-rule revalidation requirement

A change is not accepted because it "looks fixed."

The triggering rule must run again.

```text
finding
  ↓
fix
  ↓
rerun SAME rule
  ↓
PASS ?
```

If not, the finding remains open or the fix must be reverted/escalated.

This creates a direct causal link between defect, repair, and evidence.

---

## 16. Dependency-aware regression

After a parent-level change, not every proof necessarily becomes invalid.

UI-Agentic uses dependency identity to determine what must be revalidated.

Conceptually, evidence is keyed by inputs such as:

```text
subject/code
contract
rule
scenario
browser/runtime
assets/fonts
locale/DPR
checker/verifier
```

If an input changes, dependent evidence is stale.

If no relevant dependency changed, existing evidence can remain reusable.

The goal is **selective invalidation without stale PASS reuse**.

---

## 17. Coverage Ledger

The Coverage Ledger answers a different question from a quality score.

It asks:

```text
How many required obligations exist?
How many were actually tested?
How many passed?
How many failed?
How many remain unknown?
```

Conceptually:

| Dimension | Required | Tested | Pass | Fail | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Routes | n | n | n | 0 | 0 |
| States | n | n | n | 0 | 0 |
| Viewport/domain obligations | n | n | n | 0 | 0 |
| Transitions | n | n | n | 0 | 0 |
| Accessibility rules | n | n | n | 0 | 0 |
| Temporal/environmental rules | n | n | n | 0 | 0 |

The ledger cannot say a UI is aesthetically good. It says whether the declared required verification set is closed.

---

## 18. Proof levels

UI-Agentic separates proof strength from simple verdicts.

### OBSERVED

A direct measurement of a concrete rendered case.

Example:

```text
At 375 px width, this page has no horizontal overflow.
```

### BOUNDED

A demonstrated bound over a declared region.

Example conceptually:

```text
Across interval W ∈ [320, 480], overflow residual ≤ tolerance.
```

This requires more than several samples.

### CERTIFIED

A property demonstrated over the declared domain using an applicable certification method and independently checked.

A certificate is only meaningful if the checker, assumptions, and scope are explicit.

---

## 19. PASS, FAIL, and UNKNOWN

The runtime verdict model is intentionally small:

```text
PASS
FAIL
UNKNOWN
```

### PASS

Positive evidence satisfies the rule under the declared contract.

### FAIL

Valid evidence demonstrates a violation.

### UNKNOWN

The system cannot establish either valid pass or valid fail evidence.

Common reasons include:

- readiness could not be established;
- required instrumentation is unavailable;
- a checker produced no unambiguous result;
- an opaque surface cannot expose required internal geometry;
- provenance is stale or missing;
- a required proof level cannot be achieved.

A required `UNKNOWN` blocks final confirmation.

---

## 20. Trusted Verification Kernel

Strong proof should not require trusting the full complexity of the evidence generator.

An agent or solver may produce a certificate, but the system should prefer a smaller deterministic checker to validate it.

The trust bundle is:

```text
contract
+ evidence/certificate
+ explicit assumptions
+ small checker
```

This is the role of the Trusted Verification Kernel: minimize the final trusted surface.

The kernel model and current implementation are explained in [04 — Proof, Evidence, and Attestation Model](04-proof-evidence-attestation.md).

---

## 21. Mutation and tamper testing

A verifier can appear correct while silently accepting bad evidence.

UI-Agentic therefore uses failure injection to test the verifier itself.

Conceptually:

```text
known-good baseline → PASS
introduce fault      → verifier must detect it
remove fault         → PASS again
```

Examples of fault classes include:

- spacing/layout errors;
- overlay/occlusion defects;
- undersized targets;
- focus escaping a modal;
- invalid contrast;
- asynchronous layout instability;
- incorrect breakpoint behavior.

The project also tests provenance tampering so stale or modified proof artifacts cannot simply be accepted because a boolean field still says `true`.

---

## 22. Visual Acceptance Contract

Not all design quality can be reduced to formal constraints.

UI-Agentic treats subjective visual judgment explicitly instead of pretending it is mathematical proof.

A Visual Acceptance Contract can define:

- hierarchy;
- composition;
- perceived typography;
- whitespace and density;
- coherence;
- brand/imagery expectations;
- accepted references or exemplars;
- named disqualifiers.

The verdict is:

```text
ACCEPTED
REJECTED
UNKNOWN
```

Visual acceptance remains **rubric evidence**. It is never upgraded to `CERTIFIED` simply because a reviewer accepted it.

---

## 23. Final Confirmation Gate

The final gate closes the declared verification claim.

The architecture requires conditions such as:

```text
Coverage = 100% of required obligations
Required proof levels satisfied
Requirement/failure-mode traceability complete
Certificate/checker validation complete where applicable
Measurement readiness satisfied
Critical verification mutants survived = 0
Unstated proof assumptions = 0
Hard FAIL = 0
Required UNKNOWN = 0
Open regression = 0
Unrevalidated fixes = 0
Parent contract violations = 0
Required state/transition obligations complete
Required cross-layer invariants complete
Declared compliance obligations complete
Critical geometry/paint failures = 0
Critical temporal/environmental instability = 0
Visual Acceptance Contract = ACCEPTED
```

No weighted average can compensate for a hard blocker.

---

## 24. Verification Attestation

When the final gate is closed, the system can emit a Verification Attestation.

The attestation is a snapshot-bound statement.

It can include digests for:

```text
subject/build
contract
scenario set
rules/checkers
measurement kernel
trusted kernel
environment manifest
runtime identity
evidence DAG
reports
visual evidence
final gate
```

The attestation answers:

> Exactly what was verified, under what contract, with which verifier, in which environment, using which evidence?

That is much stronger and more precise than storing an independent `verified = true` field.

---

## 25. What `LOCKED` means

`LOCKED` means the attested snapshot is under controlled change.

It does **not** mean:

- immutable forever;
- universally correct;
- safe in undeclared browsers or environments;
- exempt from future regression testing.

When a relevant input changes:

```text
change
  ↓
impact analysis
  ↓
affected evidence becomes stale
  ↓
revalidation
  ↓
new attestation if closure is restored
```

This is why the project uses the principle:

> Locked means controlled change, never immutability.

---

## 26. The external-project CLI

The stable public CLI currently exposes:

```text
ui-agentic init
ui-agentic discover
ui-agentic verify
ui-agentic report
ui-agentic lock
```

### init

Creates a project verification contract.

### discover

Probes declared routes of a running HTTP application and records basic rendered facts.

### verify

Compiles the declared Supported Domain and runs browser obligations through the canonical replay engine.

### report

Displays the latest verification summary.

### lock

Exists as the final gate entry point, but the stable public external-project implementation remains deliberately fail-closed until the external subject, contract, verifier, Evidence DAG, visual review, runtime identity, and attestation provenance are all bound by one authoritative model.

Returning `NO LOCK` is intentional when the proof chain is incomplete.

---

## 27. The bundled reference implementation

The repository includes a narrow vertical slice used to prove the verification architecture itself.

It exercises multiple classes of behavior, including:

- multiple routes;
- responsive viewport widths;
- modal states;
- state transitions;
- keyboard/mouse behavior;
- composite invariants;
- mutation/fault injection;
- provenance tamper checks;
- visual evidence;
- final attestation.

Its purpose is not to claim universal UI coverage. Its purpose is to prove that the verification architecture can close a declared domain without synthetic passes.

---

## 28. Repository architecture

```text
UI-Agentic/
│
├── README.md
├── SKILL.md
├── supported-domain.yaml
│
├── ui_agentic/
│   └── external-project product surface
│
├── core/
│   ├── scenario compilation
│   ├── coverage
│   ├── replay
│   ├── evidence
│   ├── runtime identity
│   ├── measurement kernel
│   └── trust / attestation primitives
│
├── gvh/
│   └── geometric extraction and verification
│
├── rules/
│   └── verification rule definitions
│
├── references/
│   └── focused operational contracts
│
├── docs/
│   └── public architecture documentation
│
├── scripts/
│   └── strict proof and CI gates
│
├── tests/
├── evaluations/
├── assets/templates/
├── reports/
│
├── archive/
│   └── historical experiments only
│
└── .github/workflows/
    └── fail-closed proof pipeline
```

---

## 29. How to read the repository

### For a new user

Read:

1. root `README.md`;
2. this guide;
3. `GLOSSARY.md`;
4. `05-project-status-and-roadmap.md`.

### For a UI methodology contributor

Read:

1. `01-pyramidal-stabilization.md`;
2. `02-agent-architecture-and-verification.md`;
3. `references/`;
4. `SKILL.md`.

### For a verification-engine contributor

Read:

1. `02-agent-architecture-and-verification.md`;
2. `04-proof-evidence-attestation.md`;
3. `core/`;
4. `scripts/`;
5. tests and mutation gates.

### For geometry work

Read:

1. `03-geometric-visual-harness.md`;
2. `gvh/`;
3. geometry-related rules and references.

---

## 30. Architecture versus implementation

This distinction is essential.

The documentation describes the **target architecture**. The repository implements an increasing subset of that architecture.

Therefore:

```text
architectural concept ≠ automatically implemented capability
implemented reference slice ≠ automatically generalized capability
```

The status document is the bridge between the two.

Read [05 — Implementation Status and Roadmap](05-project-status-and-roadmap.md) whenever you need to know whether a capability is:

```text
IMPLEMENTED
REFERENCE IMPLEMENTATION
PARTIAL
PLANNED
```

---

## 31. Explicit non-claims

UI-Agentic does not currently claim:

- universal UI correctness;
- universal cross-browser support;
- complete WCAG conformance for arbitrary products;
- complete ACT Rules coverage;
- universal continuous responsive certification;
- certified internal geometry for opaque surfaces without instrumentation;
- automatic proof of subjective design quality;
- authoritative external-project `LOCKED` status before the complete external attestation chain is implemented.

A narrower honest contract is stronger than a broad unprovable claim.

---

## 32. The complete mental model

The entire project can be reduced to this chain:

```text
DECLARE
  What do we support?

DISCOVER
  What actually exists?

OWN
  Which hierarchy level controls each constraint?

STABILIZE
  Make parent contracts coherent before descending.

COMPILE
  Turn the Supported Domain into required obligations.

MEASURE
  Observe the real browser under controlled readiness.

VERIFY
  Run geometry, paint, interaction, accessibility, and temporal rules.

DIAGNOSE
  Find the lowest valid root-cause owner.

FIX
  Change only what should own the correction.

REVALIDATE
  Re-run the same triggering rule.

REGRESS
  Invalidate and replay dependent evidence.

CLOSE
  Reach complete required coverage with no blocking FAIL/UNKNOWN.

REVIEW
  Evaluate subjective visual quality explicitly.

ATTEST
  Bind the final verdict to the exact proof inputs.

LOCK
  Treat future changes as controlled, impact-analyzed changes.
```

That is UI-Agentic from A to Z.
