# 09 — Frequently Asked Questions

This FAQ addresses the most common misunderstandings about UI-Agentic.

For the full architecture, start with `README.md` and `docs/00-project-guide.md`.

---

## What is UI-Agentic?

UI-Agentic is an evidence-driven system for stabilizing and verifying browser interfaces under explicit contracts.

It combines:

- a hierarchy for deciding where UI properties belong;
- a Supported Domain that defines the scope of the claim;
- a Scenario Compiler that derives required obligations;
- browser-based verification;
- geometry, interaction, accessibility, paint, and temporal checks;
- content-addressed evidence;
- regression invalidation;
- visual acceptance;
- fail-closed final gates and snapshot-bound attestation.

It is both an architecture and an evolving open-source implementation.

---

## Is UI-Agentic an AI design generator?

No.

UI-Agentic can be used by an AI agent while designing or modifying an interface, but its core purpose is not to generate arbitrary designs from prompts.

Its role is closer to:

```text
agent / developer proposes a change
            ↓
UI-Agentic determines what must remain true
            ↓
verification produces evidence
            ↓
change is accepted, rejected, or left UNKNOWN
```

The AI may propose code. UI-Agentic constrains and verifies the result.

---

## Is UI-Agentic a testing framework like Playwright?

Not exactly.

UI-Agentic uses Playwright for real browser execution, but Playwright is only one layer of the system.

Playwright answers questions such as:

```text
Can I navigate here?
Can I click this?
What does the browser render?
```

UI-Agentic additionally asks:

```text
Which cases are required by the support contract?
Which rule owns this property?
What proof level is required?
Is the page ready to measure?
Can this evidence be reused?
Did the verifier detect its own critical failure modes?
Is visual review complete?
Can the final claim be attested?
```

---

## Is it a screenshot-testing tool?

No.

Screenshots are one form of evidence, especially for visual review and raster identity, but they cannot prove every UI property.

A screenshot cannot reliably establish, by itself:

- keyboard focus order;
- whether the correct element receives a pointer event;
- modal focus containment;
- semantic roles;
- state-transition correctness;
- runtime readiness;
- whether a required state was never entered.

UI-Agentic intentionally combines multiple evidence types.

---

## What does “100% confirmed” mean?

It means 100% of the **Required Scenario Set derived from the declared Supported Domain** has been closed at the required proof levels.

It does not mean the interface is correct in every imaginable browser, locale, content condition, viewport, platform, or future environment.

The claim is bounded by the contract.

Conceptually:

```text
Supported Domain
      ↓
Required Scenario Set
      ↓
all required obligations closed
      ↓
100% confirmed for that declared scope
```

---

## Why not just test every possible combination?

The full Cartesian product can be enormous or infinite.

Instead, UI-Agentic models which factors can affect each rule and compiles the rule over the relevant subspace.

For continuous or very large domains, the architecture distinguishes:

- direct observations;
- relevant classes and boundaries;
- adaptive sweeps;
- demonstrated bounds;
- property-specific certification methods;
- robustness discovery such as t-way or generative testing.

Sampling can discover failures, but it must not be mislabeled as universal proof.

---

## What is the Supported Domain?

The Supported Domain is the explicit scope of the verification claim.

It can include:

```text
routes
viewports / containers
states
transitions
content classes
input modalities
locales / direction
browsers / platforms
zoom / DPR
async / temporal conditions
compliance profiles
```

If a required product condition is outside the Supported Domain, it is outside the final claim unless the contract is expanded and reverified.

---

## What is the pyramidal hierarchy?

UI-Agentic organizes UI ownership as:

```text
GLOBAL
→ FAMILY
→ PAGE
→ SECTION
→ COMPONENT
→ STATE
→ DETAIL
```

The rule is:

> A lower-level fix must not silently destabilize a higher-level contract.

For example, if five pages have the wrong container width because the family shell is incorrect, the right fix is usually at the family level—not five page-specific overrides.

---

## What does “lowest valid owner” mean?

Fix the problem at the lowest hierarchy level capable of solving the root cause **without violating a parent contract**.

If a component-specific issue can be fixed inside that component without changing the family or page contract, the component is the valid owner.

If the component is only exposing a broken global spacing rule, the change must escalate upward.

---

## What are PASS, FAIL, and UNKNOWN?

### PASS

Valid positive evidence established the required property.

### FAIL

Valid negative evidence established a violation.

### UNKNOWN

The verifier could not establish the property at the required strength.

Examples of `UNKNOWN` include:

- required state could not be entered;
- target element is ambiguous;
- page never reached required readiness;
- internal geometry is unavailable for an opaque surface;
- required certificate cannot be checked;
- evidence binding is invalid.

A required `UNKNOWN` blocks final confirmation.

---

## Why is UNKNOWN so important?

Because the most dangerous verification error is often not a detected failure—it is a **missing proof silently treated as success**.

UI-Agentic uses `UNKNOWN` to preserve uncertainty explicitly.

```text
absence of evidence ≠ evidence of PASS
```

---

## What is Measurement Readiness?

Measurement Readiness is the gate that decides whether a rendered state is valid to measure.

Depending on the rule, it may require stable geometry, resolved fonts/assets, hydration, the correct application state, or controlled timing.

Without readiness, a browser measurement may describe a transient state rather than the state the contract intends to verify.

---

## What is the Geometric Visual Harness (GVH)?

GVH is the geometry-focused part of UI-Agentic.

It measures rendered spatial facts such as:

- position and dimensions;
- containment;
- spacing and alignment;
- group geometry;
- clipping;
- layering and occlusion signals;
- responsive relationships;
- temporal geometry.

GVH does not decide whether a design is aesthetically good.

---

## Why are there five verification layers?

Because different UI properties require different evidence.

```text
GEOMETRY
PAINT
INTERACTION
ACCESSIBILITY / SEMANTICS
TEMPORAL / ENVIRONMENTAL
```

Keeping them separate prevents invalid reasoning such as:

```text
semantic role is correct
therefore control is usable
```

or:

```text
screenshot looks correct
therefore keyboard behavior is correct
```

---

## What is a cross-layer invariant?

A property that requires evidence from more than one verification layer.

Examples:

### `TARGET_OPERABLE`

A target must have usable geometry and actually receive the intended interaction.

### `FOCUS_USABLE`

Focus must move correctly and the focused control must remain usable and perceptible.

### `MODAL_INTEGRITY`

A modal must satisfy geometry, focus, background operability, and interaction invariants together.

Cross-layer invariants still produce one atomic verdict.

---

## What are OBSERVED, BOUNDED, and CERTIFIED?

They are proof strengths.

### OBSERVED

Direct measurement of a declared case.

### BOUNDED

A demonstrated bound over a declared region.

### CERTIFIED

A property established by an applicable certification method and independently checked.

A thousand observations remain observations unless a valid method turns them into a demonstrated bound.

---

## What is the Evidence DAG?

The Evidence DAG is the content-addressed graph of proof artifacts and their dependencies.

Evidence identity can include:

```text
subject / code
contract
rule
scenario
browser / environment
fonts / assets
verifier / checker
readiness inputs
```

This enables sound dependency-aware regression: reuse evidence only when the inputs that justify it remain compatible.

---

## Why does UI-Agentic test the verifier with mutants?

A green verifier can still be wrong.

Mutation/fault injection deliberately creates known defects and requires the verifier to detect them.

If a critical mutant survives, the verifier has demonstrated a blind spot and the final claim should not ignore that fact.

---

## Is mutation testing proof that the verifier is complete?

No.

Mutation testing establishes adequacy only against the declared injected failure modes.

It is evidence that specific blind spots are not present—not proof that no unknown blind spot can exist.

---

## What is Visual Acceptance?

Visual Acceptance is the explicit rubric-based review for properties that are not fully reducible to deterministic rules.

It can consider:

- hierarchy;
- composition;
- perceived typography;
- density and whitespace;
- visual coherence;
- brand fidelity;
- reference alignment.

Its verdict is:

```text
ACCEPTED | REJECTED | UNKNOWN
```

Visual Acceptance is subjective evidence with explicit scope. It is not `CERTIFIED` proof.

---

## Why have both exact screenshot hashes and a review fingerprint?

They serve different purposes.

### Exact screenshot hashes

Prove the exact bytes of the current-run visual artifacts.

### Review fingerprint

May allow reuse of a visual review across a narrowly defined equivalence class when the project has explicitly demonstrated that tiny renderer noise should not invalidate subjective approval.

The equivalence mechanism must be conservative and adversarially tested. It must never replace exact artifact identity.

---

## What does LOCKED mean?

`LOCKED` means an identified snapshot satisfied the declared final confirmation contract and the verdict is bound to the proof bundle used to justify it.

It does not mean the code is frozen forever.

```text
change
→ impact analysis
→ invalidate affected evidence
→ reverify
→ issue a new attestation
```

Locked means controlled change.

---

## Does a LOCKED commit make future commits LOCKED?

No.

Attestations are snapshot-bound.

A later commit must establish its own compatible evidence and final gate.

---

## Is the Git repository itself the attestation?

No.

The repository contains the implementation and proof tooling. The authoritative attestation for a run is a generated artifact bound to the exact verified snapshot and run inputs.

A committed static JSON file cannot safely act as a timeless claim about every future repository state.

---

## Is UI-Agentic WCAG 2.2 AA certified?

No universal claim is made.

The project implements selected accessibility and cross-layer checks, but complete WCAG conformance requires explicit scope, applicability, normative requirement closure, and evidence across the target product.

Any future conformance claim must name the standard, version, level, product scope, and verification coverage.

---

## Does UI-Agentic support Firefox and WebKit?

The architecture supports multi-browser domains conceptually, but the current primary executable path is Chromium through Playwright.

See `docs/05-project-status-and-roadmap.md` for the current implementation boundary.

---

## Does it prove every viewport between mobile and desktop widths?

Not universally today.

The architecture supports continuous-domain reasoning and adaptive boundary analysis, but the current reference implementation is narrower and uses declared discrete viewport obligations for many rules.

A discrete viewport matrix should not be described as continuous responsive certification.

---

## Can it verify canvas, WebGL, or cross-origin internals?

Only to the degree those internals are observable through a trusted adapter or instrumentation contract.

The external box of an opaque surface can often be measured. Internal geometry cannot be called certified if the verifier cannot observe it.

The correct result for required unavailable internals is `UNKNOWN`.

---

## Can UI-Agentic automatically fix every failure?

No.

UI-Agentic defines a repair discipline and can guide an agent toward the valid owner and required regression path, but the current product is not a universal autonomous repair engine for arbitrary applications.

Its primary strength today is making the verification claim explicit and fail-closed.

---

## How does an AI agent use UI-Agentic?

The agent begins with `SKILL.md`.

The skill router selects the smallest relevant references and rules based on:

```text
operating mode
+ hierarchy level
+ failure signal
+ verification layer
```

The agent can then:

```text
discover
→ diagnose
→ modify
→ verify
→ revalidate same rule
→ run regression
```

The agent does not get authority to declare `PASS` merely because it generated the change.

---

## Can I use it on my own application today?

Yes, for the currently implemented external-project verification surface.

The public CLI includes commands such as:

```text
ui-agentic init
ui-agentic discover
ui-agentic verify
ui-agentic report
ui-agentic lock
```

The external `lock` command remains deliberately fail-closed until the full external attestation chain is authoritative.

Read `docs/06-using-ui-agentic.md` before interpreting external verification output as equivalent to the bundled reference `LOCKED` path.

---

## Why is the project conservative about claims?

Because verification systems become dangerous when their confidence language is broader than their evidence.

UI-Agentic deliberately prefers:

```text
UNKNOWN
```

over:

```text
probably fine
```

when the required property cannot be established.

---

## Is the architecture finished?

The core architecture is extensively specified, and the bundled reference pipeline demonstrates many of its trust principles in executable CI.

The general product is still being expanded.

Areas such as broader external attestation, multi-browser support, richer accessibility coverage, continuous responsive proofs, opaque-surface adapters, and deeper temporal verification remain broader targets.

See `docs/05-project-status-and-roadmap.md` for the current status rather than inferring maturity from the size of the architecture documents.

---

## Where should I start?

### I want the shortest explanation

Read `README.md`.

### I want the complete mental model

Read `docs/00-project-guide.md`.

### I want to understand the source code

Read `docs/07-codebase-and-runtime-flow.md`.

### I want to contribute a new verifier capability

Read `docs/08-extending-ui-agentic.md` and `CONTRIBUTING.md`.

### I want exact terminology

Read `docs/GLOSSARY.md`.

### I want to know what is really implemented

Read `docs/05-project-status-and-roadmap.md`.
