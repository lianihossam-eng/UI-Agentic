# UI-Agentic

**Evidence-driven UI stabilization and verification for browser applications.**

UI-Agentic is an open-source system for reasoning about interface quality as a set of explicit contracts, measurable obligations, and reproducible evidence.

Instead of treating a UI as a collection of isolated screenshots, UI-Agentic treats it as a hierarchy of dependent design decisions and runtime states:

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

Its central rule is simple:

> A lower-level fix must not silently destabilize a higher-level contract.

UI-Agentic combines three ideas:

1. **Pyramidal stabilization** — establish shared design constraints before polishing local details.
2. **Browser verification** — execute explicit obligations against the rendered application rather than relying on source inspection alone.
3. **Evidence and attestation** — bind results to the exact subject, contract, verifier, environment, and visual review inputs that produced them.

The project is intentionally conservative about claims. A `PASS` means that a specific rule produced valid positive evidence. A required case with missing or invalid evidence becomes `UNKNOWN`. A final `LOCKED` verdict is allowed only when the declared verification contract is fully closed for the attested snapshot.

---

## What problem does UI-Agentic solve?

Interface work tends to fail in two different ways.

### 1. Local fixes create global drift

A developer changes a component to solve one screen. Another screen inherits the change and breaks. A page adds a custom breakpoint because the family layout is weak. A section introduces a new spacing value because the global spacing system does not quite fit.

Over time, the interface still "works", but the design system becomes an accumulation of exceptions.

UI-Agentic addresses this with explicit ownership:

```text
Global contract
   ↓
Family contract
   ↓
Page contract
   ↓
Section / component contracts
   ↓
State and detail rules
```

Every important property belongs to a level. Fixes are applied at the **lowest valid owner** that can solve the root cause without violating its parent.

### 2. Automated UI checks can overstate confidence

A few screenshots can look clean while keyboard focus is wrong. An accessibility tree can look correct while a target is visually occluded. A page can pass at three widths while failing at an untested responsive boundary. A test suite can report green even though required states were never exercised.

UI-Agentic therefore begins with a **Supported Domain**: an explicit statement of what the product claims to support.

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

That domain is compiled into the set of required verification obligations. The final claim is bounded by that contract.

> **100% confirmed means 100% of the required obligations derived from the declared Supported Domain, with every required proof level satisfied.**

It does not mean "correct in every imaginable environment."

---

## The project in one diagram

```text
                          ┌──────────────────────────┐
                          │     SUPPORTED DOMAIN     │
                          │ routes · states · inputs │
                          │ viewports · locale · time│
                          └────────────┬─────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │    SCENARIO COMPILER     │
                          │ dependency-aware required│
                          │ verification obligations │
                          └────────────┬─────────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
                 ▼                     ▼                     ▼
        ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
        │   GEOMETRY     │    │ INTERACTION /  │    │ PAINT / A11Y / │
        │      GVH       │    │    STATES      │    │ TEMPORAL LAYERS│
        └───────┬────────┘    └───────┬────────┘    └───────┬────────┘
                └─────────────────────┼─────────────────────┘
                                      │
                                      ▼
                          ┌──────────────────────────┐
                          │      EVIDENCE DAG        │
                          │ content-addressed proof  │
                          └────────────┬─────────────┘
                                       │
                  ┌────────────────────┼────────────────────┐
                  │                    │                    │
                  ▼                    ▼                    ▼
          Coverage Ledger      Visual Acceptance     Mutation / tamper
          & traceability          Contract               gates
                  └────────────────────┼────────────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │ FINAL CONFIRMATION GATE  │
                          └────────────┬─────────────┘
                                       │
                              PASS only if closed
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │ VERIFICATION ATTESTATION │
                          │         LOCKED           │
                          └──────────────────────────┘
```

---

## The A-to-Z workflow

The complete method is intentionally ordered. Structural work comes before local polish, and evidence comes before confidence claims.

```text
0.  Declare the Supported Domain
1.  Discover the product
2.  Establish or extract the global design contract
3.  Stabilize the global design system
4.  Stabilize page families
5.  Stabilize page structures
6.  Stabilize sections, components, states, and transitions
7.  Run five-layer verification
8.  Classify findings with owner and evidence
9.  Diagnose the root cause
10. Fix at the lowest valid owner
11. Re-run the same triggering rule
12. Run dependency-aware regression
13. Close required coverage
14. Perform visual acceptance review
15. Run the final confirmation gate
16. Emit a verification attestation
17. Lock the verified snapshot
```

A lower step cannot compensate for a failure above it. Visual polish cannot hide broken interaction, missing coverage, invalid geometry, or an unresolved `UNKNOWN`.

For the full walkthrough, read **[Project Guide: UI-Agentic from A to Z](docs/00-project-guide.md)**.

---

## The three core specifications

UI-Agentic separates the architecture into three independent responsibilities.

| Specification | Purpose |
| --- | --- |
| **[01 — Pyramidal UI Stabilization System](docs/01-pyramidal-stabilization.md)** | Defines hierarchy, ownership, stabilization states, change boundaries, escalation, and regression. |
| **[02 — UI Agent Architecture & Verification](docs/02-agent-architecture-and-verification.md)** | Defines orchestration, Supported Domain compilation, verification layers, evidence, proof requirements, gates, and ledgers. |
| **[03 — Geometric Visual Harness](docs/03-geometric-visual-harness.md)** | Defines objective geometry extraction, spatial constraints, responsive analysis, clipping, layering, occlusion, and geometric regression. |

Two additional documents describe the trust model and current implementation boundary:

- **[04 — Proof, Evidence, and Attestation Model](docs/04-proof-evidence-attestation.md)**
- **[05 — Implementation Status and Roadmap](docs/05-project-status-and-roadmap.md)**

A project-wide vocabulary is available in **[Glossary](docs/GLOSSARY.md)**.

---

## Five verification layers

UI-Agentic keeps different verification concerns separate because one kind of success cannot prove another.

| Layer | Verifies |
| --- | --- |
| **Geometry** | position, size, containment, alignment, gaps, clipping, responsive structure, layers, occlusion |
| **Paint** | rendered typography, colors, contrast, borders, shadows, opacity, masks, raster fidelity |
| **Interaction** | hit testing, pointer/touch behavior, keyboard behavior, focus, scrolling, state transitions |
| **Accessibility / Semantics** | roles, accessible names, reading order, focus order, state semantics, reduced-motion behavior |
| **Temporal / Environmental** | fonts, assets, hydration, async state, animation, browser/runtime identity, layout stability |

The **Geometric Visual Harness (GVH)** owns geometry. The UI-Agentic orchestrator coordinates all five layers.

Some properties cross multiple layers. These are checked as composite invariants rather than pretending that a single layer is enough. Examples include:

```text
TARGET_OPERABLE
FOCUS_USABLE
MODAL_INTEGRITY
VISUAL_SEMANTIC_ORDER
ASYNC_STABILITY
```

For example, a control can have the correct semantic role and still be unusable because another element intercepts pointer events. A modal can be visually centered and still fail because keyboard focus escapes into the page behind it.

---

## Proof model

UI-Agentic distinguishes three proof levels.

```text
OBSERVED
  Direct measurement of a rendered case.

BOUNDED
  A demonstrated bound over a declared region of the domain.

CERTIFIED
  A property demonstrated over the declared domain by an applicable
  certification method and independently checked.
```

These levels are not interchangeable.

A large number of samples is still sampling. It does not automatically become a mathematical bound. A screenshot matrix does not automatically become a certificate.

The verdict model is fail-closed:

```text
valid positive evidence    → PASS
valid negative evidence    → FAIL
missing or invalid evidence→ UNKNOWN
required UNKNOWN           → blocks confirmation
```

---

## Evidence, provenance, and trust

The system treats evidence producers as potentially fallible. An agent, solver, search procedure, or fuzzer does not become trusted merely because it produced a result.

The intended strong-proof trust bundle is:

```text
contract
+ evidence or certificate
+ small deterministic checker
+ explicit assumptions
```

Evidence is content-addressed. Conceptually, an evidence key binds the relevant inputs:

```text
hash(
  subject / code identity
+ contract
+ rule
+ scenario
+ browser and platform
+ fonts and assets
+ locale and DPR
+ verifier / checker identity
)
```

If one of those inputs changes, dependent evidence becomes stale and must be revalidated.

This is the basis of **dependency-aware regression**: re-run what became invalid, not everything blindly, while never reusing proof across incompatible snapshots.

---

## What `LOCKED` means

`LOCKED` is not a permanent boolean and it does not mean the UI can never change.

A `LOCKED` result means that an identified snapshot satisfied the declared confirmation contract and that the verdict is bound to the evidence and environment that justified it.

An authoritative attestation can bind:

```text
subject / build identity
contract identity
compiled scenario set
rules and checkers
measurement kernel
trusted verification kernel
environment manifest
runtime identity
Evidence DAG root
report root
visual evidence root
final gate
```

When a relevant input changes, the corresponding proof becomes stale. The correct response is impact analysis and revalidation, not silent reuse of the old verdict.

> **Locked means controlled change, never immutability.**

---

## Current implementation status

The repository contains two related things:

1. a **general architecture** for evidence-driven UI stabilization and verification; and
2. a **working reference implementation** that proves increasingly large parts of that architecture in executable browser runs.

The bundled reference path includes Playwright/Chromium replay, scenario compilation, coverage tracking, measurement readiness, cross-layer checks, mutation/fault injection, provenance checks, visual acceptance, and a strict CI attestation path.

The external-project CLI is intentionally more conservative. In the stable public version it can initialize a contract, discover declared routes, execute browser verification, and report results, but the external `lock` path remains fail-closed until all required external subject, contract, verifier, evidence, visual-review, and runtime provenance are bound by the same authoritative attestation model.

See **[Implementation Status and Roadmap](docs/05-project-status-and-roadmap.md)** before interpreting an architectural concept as a universal current capability.

---

## Quick start

### Requirements

- Python 3.10+
- Playwright
- Chromium installed through Playwright

### Install for local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
playwright install chromium
```

On Windows, use the appropriate virtual-environment activation command for your shell.

### Run the bundled reference verifier

```bash
python run_goal_verify.py
```

This command is useful for local inspection. The repository's complete GitHub Actions workflow performs additional mutation, provenance, runtime, visual, and attestation gates.

### Use UI-Agentic against a running local application

Initialize a project contract:

```bash
ui-agentic init --project . --base-url http://127.0.0.1:3000
```

Probe the declared routes:

```bash
ui-agentic discover --project .
```

Run browser verification:

```bash
ui-agentic verify --project .
```

Read the latest summary:

```bash
ui-agentic report --project .
```

Attempt the external lock gate:

```bash
ui-agentic lock --project .
```

The current stable external lock path is deliberately fail-closed rather than issuing a stronger claim than the evidence model can support.

---

## Repository map

```text
UI-Agentic/
├── README.md                    Public entry point
├── SKILL.md                     Agent routing and workflow contract
├── supported-domain.yaml        Reference Supported Domain
│
├── ui_agentic/                  External-project CLI and adapters
├── core/                        Scenario, coverage, evidence, replay, trust
├── gvh/                         Geometry extraction and verification
│
├── docs/                        Public architecture documentation
├── references/                  Focused operational references
├── rules/                       Verification rule definitions
│
├── scripts/                     CI and proof-gate tooling
├── evaluations/                 Evaluation fixtures
├── tests/                       Verifier tests
├── assets/templates/            Bundled reference application surfaces
├── reports/                     Review inputs / reference proof artifacts
│
├── archive/                     Historical experiments; non-normative
└── .github/workflows/           Fail-closed proof pipeline
```

### Source-of-truth rule

For a specific release or commit:

- architecture documents explain the intended system;
- the status document says what is implemented versus planned;
- executable code and CI are the auditable source for actual behavior;
- `archive/` is historical and must not be treated as normative architecture.

---

## Documentation paths

### If you are new to the project

1. Read this README.
2. Read **[Project Guide: UI-Agentic from A to Z](docs/00-project-guide.md)**.
3. Use **[Glossary](docs/GLOSSARY.md)** when a project term is unfamiliar.
4. Read **[Implementation Status and Roadmap](docs/05-project-status-and-roadmap.md)**.

### If you are implementing or modifying UI-Agentic

1. **[Pyramidal Stabilization](docs/01-pyramidal-stabilization.md)**
2. **[Agent Architecture & Verification](docs/02-agent-architecture-and-verification.md)**
3. **[Proof, Evidence, and Attestation](docs/04-proof-evidence-attestation.md)**
4. **[Contributing Guide](CONTRIBUTING.md)**

### If you are working on geometry

Read **[Geometric Visual Harness](docs/03-geometric-visual-harness.md)** and the focused references under `references/`.

The full documentation index is in **[docs/README.md](docs/README.md)**.

---

## What UI-Agentic does not claim

The project does not claim:

- universal correctness for arbitrary interfaces;
- complete WCAG conformance for arbitrary products;
- complete ACT Rules coverage;
- multi-browser certification by default;
- universal continuous responsive certification for every rule;
- internal geometry certification for opaque canvas, WebGL, video, or inaccessible cross-origin internals without instrumentation;
- automatic proof that subjective design intent is aesthetically good;
- authoritative external-project `LOCKED` status before the full external attestation chain is implemented and closed.

Every confidence claim must remain inside the declared contract and available proof.

---

## Project principles

The project follows a small set of non-negotiable principles:

1. **Top-down constraints.**
2. **Breadth before depth.**
3. **Fix at the lowest valid owner.**
4. **Escalate upward only when necessary.**
5. **Regress downward after parent changes.**
6. **Evidence before failure claims.**
7. **Required `UNKNOWN` blocks confirmation.**
8. **A fix must revalidate the same triggering rule.**
9. **Geometry, paint, interaction, semantics, and time remain distinct concerns.**
10. **No silent local patching.**
11. **No aggregate score may hide a hard failure.**
12. **`100%` always means 100% of the required scenario set derived from the declared Supported Domain.**
13. **`LOCKED` always refers to an identified attested snapshot.**

---

## Contributing and security

Contributions are welcome, especially when they improve measurable verification coverage without weakening fail-closed behavior.

- Read **[CONTRIBUTING.md](CONTRIBUTING.md)** before submitting architectural or verifier changes.
- Read **[SECURITY.md](SECURITY.md)** for vulnerability reporting.
- Community behavior is governed by **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)**.

UI-Agentic is released under the **MIT License**.
