# UI-Agentic Glossary

This glossary defines the project terms used across the public documentation, code, rules, reports, and CI gates.

Terms are intentionally precise because UI-Agentic uses them as parts of verification contracts rather than as loose marketing language.

---

## Architecture and hierarchy

### Global

The highest UI ownership level. It owns product-wide design decisions such as typography, semantic colors, spacing scales, radii, elevation, shared primitives, and global responsive philosophy.

### Family

A group of related pages that share structural behavior such as an application shell, navigation, common header, content container, density model, or responsive transformation.

### Page

A single product surface with a user goal, information hierarchy, macro layout, actions, page-specific states, and business constraints.

### Section

A structural region inside a page, such as a toolbar, grid, summary block, table region, or content group.

### Component

A reusable UI unit with its own anatomy, variants, dimensions, internal spacing, and states.

### State

A concrete UI condition such as `default`, `loading`, `error`, `selected`, `disabled`, or `modal-open`.

### Detail

Fine visual polish such as optical alignment, micro-spacing, icon weight, subtle border treatment, and motion timing. Detail changes must not alter an already stabilized parent structure.

### Owner

The hierarchy level responsible for a property or finding. Every important constraint should have a primary owner.

### Lowest valid owner

The lowest hierarchy level that can correct a root cause without violating a parent contract.

### Upward escalation

Moving a change request from a lower owner to a higher owner when the lower level cannot solve the problem safely.

### Downward regression

Revalidating affected descendants after a parent-level contract changes.

---

## Stabilization

### UNEXPLORED

The scope has not been sufficiently discovered or mapped.

### DRAFT

A direction exists, but structural decisions are still fluid.

### STRUCTURED

The architecture and relationships are defined, but major changes are still allowed.

### STABLE

The scope is coherent enough to allow work to continue safely at lower levels.

### VERIFIED

Applicable verification obligations have passed with the required evidence.

### LOCKED

The verified snapshot is bound to an attestation and future changes require impact analysis and controlled revalidation. `LOCKED` does not mean immutable.

### Breadth before depth

The rule that representative global, family, and page structures should be stabilized across the product before deeply polishing one isolated surface.

### Change Boundary System

The ownership and escalation rules that prevent a local fix from silently modifying constraints owned by a parent level.

---

## Scope and compilation

### Supported Domain

The explicit set of product conditions covered by a verification claim. It can include routes, viewport/container sizes, content classes, UI states, inputs, locales, browsers, DPR, time, async scenarios, and compliance profiles.

### Required Scenario Set

The set of verification obligations compiled from the Supported Domain, rules, dependencies, contracts, and boundaries.

### Scenario Compiler

The component that derives required verification obligations from the Supported Domain. It uses rule dependencies so unrelated factors do not produce unnecessary Cartesian expansion.

### Dependency hypergraph

A representation of which factors, rules, contracts, and outputs depend on one another. It is used to compile obligations and later to invalidate only affected evidence.

### Boundary

A value or region where behavior may change, such as a responsive width, content threshold, state transition, or constraint limit.

### Robustness discovery

Additional exploration used to find interactions not already modeled by the required scenario set. Techniques may include t-way combinations, property-based generation, or fuzzing. Discovery does not automatically become certification.

### Content Domain

The declared classes, extremes, and invariants of user/content data that can affect UI behavior.

### State Transition Model

A model of interactive behavior expressed conceptually as:

```text
State --event [guard] / effect--> State
```

It defines reachable states, required and forbidden transitions, guards, round trips, and relevant temporal invariants.

---

## Verification layers

### Geometry

Verification of position, size, grouping, spacing, containment, clipping, responsive layout, stacking, occlusion, and related spatial properties.

### Paint

Verification of rendered visual properties such as typography, colors, contrast, borders, shadows, opacity, masks, and raster fidelity.

### Interaction

Verification of hit testing, pointer/touch behavior, keyboard operation, focus behavior, scrolling, gestures, and state transitions.

### Accessibility / Semantics

Verification of roles, accessible names, state semantics, reading order, focus order, keyboard behavior, and related semantic properties.

### Temporal / Environmental

Verification of time- and environment-dependent behavior such as fonts, assets, hydration, asynchronous transitions, animation, virtualization, layout stability, browser/runtime identity, locale, and DPR.

### Cross-layer invariant

A property that requires evidence from more than one verification layer and must be evaluated as one composite contract.

### TARGET_OPERABLE

A composite invariant that checks whether an interactive target is geometrically sufficient, visible/non-critically-occluded, and actually receives the intended hit test.

### FOCUS_USABLE

A composite invariant that combines correct focus behavior, keyboard semantics, visibility, and a perceptible focus indicator.

### MODAL_INTEGRITY

A composite invariant for modal behavior, potentially combining overlay geometry/layering, focus containment/return, background non-operability, transitions, and temporal stability.

### VISUAL_SEMANTIC_ORDER

A composite invariant that checks whether visual ordering remains compatible with declared reading and focus order.

### ASYNC_STABILITY

A composite invariant that checks whether an asynchronous transition reaches a correct, visible, operable, geometrically stable final state.

---

## Geometry and GVH

### GVH

**Geometric Visual Harness.** The objective geometry measurement subsystem inside UI-Agentic.

### Geometry IR

A serializable intermediate representation of rendered spatial information and constraints. It can include viewport information, boxes, fragments, transforms, clipping, coordinate chains, layer relationships, groups, and constraint metadata.

### Spatial Precision Ladder

The conceptual levels of geometric precision:

```text
L0 — layout box
L1 — fragments
L2 — transformed region
L3 — clipped / visible region
L4 — layered region / occlusion relationships
```

### Scene graph

A hierarchical representation of rendered UI elements and their spatial relationships.

### Layer graph

A partial ordering of stacking contexts, paint order, clipping, and occlusion relationships. It is not a single global numeric `z` axis.

### Residual

The measured difference between an actual geometric value and the target/constraint value.

### Stability Margin

The distance from the current valid geometry to the nearest known violation boundary. A passing state with a very small margin is considered fragile.

### Geometric fingerprint

A structural representation of a rendered page used to explain spatial drift, including hierarchy, normalized boxes, gaps, alignment axes, topology, layer relations, and related geometry.

### Opaque surface

A surface such as canvas, WebGL, video, or inaccessible cross-origin internals whose external box may be measurable while internal geometry requires additional instrumentation or adapters.

---

## Evidence and proof

### Evidence

The recorded data that supports a verification result. Evidence can be static, rendered, or rubric-based.

### Evidence DAG

A content-addressed dependency graph of evidence. Evidence reuse is valid only when the relevant inputs and dependencies remain identical.

### Evidence key

A digest derived from inputs such as subject/code identity, contract, rule, scenario, environment, assets/fonts, and verifier/checker identity.

### Proof level

The strength of evidence required by a rule: `OBSERVED`, `BOUNDED`, or `CERTIFIED`.

### OBSERVED

Direct measurement of a concrete rendered or static case.

### BOUNDED

A demonstrated bound over a declared region of the domain. Several samples do not automatically establish a bound.

### CERTIFIED

A property demonstrated over the declared domain by an applicable method and independently checked.

### Proof source

The origin of a proof, for example `execution`, `model`, or `hybrid`.

### Certificate

A proof artifact or witness that can be validated independently by a checker.

### Checker

A small deterministic validator that verifies a certificate or proof artifact without reproducing the full evidence-generation process.

### Trusted Verification Kernel

The smallest intended trusted surface for strong proof claims: contract, evidence/certificate, explicit assumptions, and independent checker logic.

### Assumption

An explicit condition under which a proof or verification result is valid. Hidden assumptions are not acceptable for final confirmation.

---

## Runtime verdicts and gates

### PASS

Valid positive evidence satisfies a rule under the declared contract.

### FAIL

Valid evidence demonstrates that a rule is violated.

### UNKNOWN

The verifier cannot establish a valid `PASS` or `FAIL`. Required `UNKNOWN` results block final confirmation.

### Fail-closed

A verification policy where missing, stale, invalid, ambiguous, or unverifiable evidence does not become a pass by default.

### Measurement Readiness Gate

The gate that establishes whether the rendered application is in a valid state for measurement: expected state reached, fonts/assets resolved as declared, hydration/async behavior settled, geometry stable, and relevant environment controls established.

### Coverage Ledger

A ledger that records required, tested, passed, failed, and unknown obligations. It measures verification closure, not subjective quality.

### Final Confirmation Gate

The final set of hard closure conditions required before an authoritative verification attestation can be emitted.

### Blocking gate

Any required gate whose failure or unknown state prevents final confirmation.

---

## Findings, repair, and regression

### Finding

A specific detected verification problem with an ID, owner, layer, expected value/behavior, actual value/behavior, evidence, proof level, and status.

### Diagnosis Gate

The step that analyzes correlated failures before applying fixes. It may use dependency slicing, delta debugging, conflict-core reduction, and owner inference.

### Dependency slice

The subset of inputs and nodes capable of influencing the failing observation.

### Delta debugging

A reduction technique that repeatedly removes parts of a scenario, content set, or change until a smaller reproducer remains.

### Conflict core

A subset of formalized constraints that remains mutually incompatible. A raw solver `unsat core` is not automatically minimal.

### Same-rule revalidation

The requirement that after a fix, the exact rule that triggered the finding must run again before the finding can close.

### Regression

Re-execution of verification obligations whose inputs or dependencies changed.

### Stale evidence

Evidence whose identity no longer matches the current subject, contract, environment, verifier, or other declared dependency.

---

## Visual review

### Visual Acceptance Contract

An explicit rubric for subjective final visual review. It can include hierarchy, composition, typography, density, coherence, brand/imagery, references, and disqualifiers.

### Visual acceptance

The subjective review stage that produces `ACCEPTED`, `REJECTED`, or `UNKNOWN` against the Visual Acceptance Contract.

### Visual evidence root

A digest that identifies the visual evidence set associated with the final review.

### Review fingerprint

A deterministic visual identity used only when the project explicitly permits review reuse across a declared raster-equivalence class. Exact screenshot identity and review identity remain separate concepts.

---

## Attestation and identity

### Subject

The exact application, build, repository state, or artifact being verified.

### Contract

The normative verification scope and requirements that define what the subject is expected to satisfy.

### Verifier

The UI-Agentic code and checker logic used to produce and validate evidence.

### Environment manifest

The recorded environment identity relevant to the verification run, such as browser/runtime/platform/tool versions and other controlled inputs.

### Runtime identity

A content/runtime identity for the actual executable browser/toolchain used during verification.

### Verification Attestation

The final snapshot-bound statement that binds the subject, contract, verifier, environment, evidence roots, reports, visual review, and final gate.

### Attestation digest

The content digest identifying the attestation payload.

### LOCKED

The verdict for an attested snapshot whose required verification claim is closed. A future relevant change invalidates affected proof and requires controlled revalidation.

### Controlled change

The process applied after a locked snapshot changes: impact analysis, evidence invalidation, targeted regression, and a new attestation if closure is restored.

---

## Project status terms

### IMPLEMENTED

Executable behavior available in the public repository.

### REFERENCE IMPLEMENTATION

Implemented and exercised by the bundled vertical slice, but not necessarily generalized to arbitrary external projects.

### PARTIAL

A meaningful subset exists, but the target architecture is broader.

### PLANNED

Defined by the architecture but not yet available as a complete public path.

### Normative

A source that defines the current intended architecture or contract.

### Non-normative

Historical, illustrative, experimental, or explanatory content that must not override the current source of truth.

---

## Related documents

- [Project Guide — UI-Agentic from A to Z](00-project-guide.md)
- [01 — Pyramidal UI Stabilization System](01-pyramidal-stabilization.md)
- [02 — UI Agent Architecture & Verification](02-agent-architecture-and-verification.md)
- [03 — Geometric Visual Harness](03-geometric-visual-harness.md)
- [04 — Proof, Evidence, and Attestation Model](04-proof-evidence-attestation.md)
- [05 — Implementation Status and Roadmap](05-project-status-and-roadmap.md)
