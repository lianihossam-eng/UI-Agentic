# 07 — Codebase and Runtime Flow

This document connects the public architecture to the actual repository layout.

If the conceptual documentation answers **what UI-Agentic means**, this document answers **where that meaning is implemented and what happens at runtime**.

It is intended for maintainers, reviewers, contributors, and anyone auditing the implementation behind a verification claim.

---

## 1. The repository has four major responsibilities

UI-Agentic is easier to understand when the codebase is divided into four functional areas:

```text
METHOD / CONTRACTS
    ↓
COMPILATION / ORCHESTRATION
    ↓
BROWSER MEASUREMENT / VERIFICATION
    ↓
EVIDENCE / GATES / ATTESTATION
```

The corresponding repository areas are:

```text
docs/ + references/ + rules/
        ↓
core/scenario_compiler.py + SKILL.md
        ↓
core/replay_engine.py + gvh/
        ↓
core/coverage.py + scripts/ + CI
```

A fifth area, `ui_agentic/`, exposes the external-project developer interface.

---

## 2. Top-level map

```text
UI-Agentic/
├── README.md
├── SKILL.md
├── supported-domain.yaml
│
├── ui_agentic/
├── core/
├── gvh/
│
├── docs/
├── references/
├── rules/
│
├── scripts/
├── tests/
├── evaluations/
│
├── assets/templates/
├── reports/
├── archive/
│
└── .github/workflows/
```

### `README.md`

Public entry point. It should explain the product without assuming prior knowledge of the research history.

### `SKILL.md`

Agent-facing routing contract. It defines how an AI agent should choose modes, hierarchy levels, references, and rules without loading the entire repository into context.

`SKILL.md` is not the full architecture specification. It is the router into the architecture.

### `supported-domain.yaml`

Reference Supported Domain for the bundled executable slice.

It defines the support boundary against which the required scenario set is compiled. A claim such as `100% confirmed` has no meaning outside an explicit support contract.

### `ui_agentic/`

External-project product surface.

This package contains the CLI and application-adapter logic used to target a running application rather than only the bundled reference fixtures.

### `core/`

Verification orchestration and proof infrastructure.

This directory owns scenario compilation, browser replay orchestration, coverage, evidence identity, trust-kernel identity, runtime identity, and attestation primitives.

### `gvh/`

Geometric Visual Harness implementation.

This directory extracts rendered geometry and evaluates geometry-related and selected cross-layer constraints against the actual browser state.

### `docs/`

Human-readable public architecture.

These documents explain the methodology, verification model, geometry model, proof model, implementation status, usage, codebase, and extension model.

### `references/`

Focused operational references used by humans and agents.

They are intentionally narrower than the core specifications. They should clarify one workflow concern without becoming competing sources of truth.

### `rules/`

Verification rule definitions and rule contribution model.

A rule should represent one stable verification obligation with an explicit owner, layer, applicability model, proof requirement, and pass condition.

### `scripts/`

Deterministic CI and proof-gate tooling.

These scripts build reports, validate bindings, inject verifier faults, enforce visual review, finalize attestations, and independently re-check critical proof artifacts.

### `tests/`

Unit and contract tests for the verifier itself.

Tests here are not a substitute for the browser proof pipeline. They protect verifier behavior, rule compilation, trust boundaries, and known invariants.

### `evaluations/`

Evaluation fixtures for routing, hierarchy, coverage, stability, regression, and visual-fidelity behavior.

### `assets/templates/`

Bundled reference application surfaces.

These are deliberately bounded fixtures used to prove the verification pipeline end to end. They are not presented as a general benchmark for web applications.

### `reports/`

Reference proof inputs and generated report locations used by the bundled pipeline.

A generated report is authoritative only when its current-run bindings and independent gates validate it.

### `archive/`

Historical experiments.

Nothing in `archive/` is normative. Historical scripts may contain earlier assumptions or incomplete designs and must not be used as the source of current project behavior.

### `.github/workflows/`

Public fail-closed CI path.

The workflow is part of the trust surface because it determines which checks must pass before an attestation can be accepted.

---

## 3. Runtime path: from contract to evidence

The core runtime flow is:

```text
Supported Domain
      ↓
Scenario Compiler
      ↓
Required Scenario Set
      ↓
Browser Replay
      ↓
Measurement Readiness
      ↓
Geometry / Paint / Interaction / A11y / Temporal checks
      ↓
PASS / FAIL / UNKNOWN records
      ↓
Coverage Ledger + Evidence DAG
      ↓
Independent proof gates
      ↓
Visual Acceptance
      ↓
Final Confirmation Gate
      ↓
Verification Attestation
      ↓
LOCKED
```

Each step has a separate responsibility.

---

## 4. Step 1 — Supported Domain

The Supported Domain declares what the verification claim covers.

Typical factors include:

```text
routes
viewports
containers
content classes
states
state transitions
input modalities
locales / direction
browser / platform
zoom / DPR
time / async behavior
```

The domain is not documentation decoration. It is an input to proof compilation.

If a factor is required by the product but omitted from the domain, the verification claim is incomplete. If a factor is intentionally unsupported, it should be declared outside the supported contract rather than silently ignored.

---

## 5. Step 2 — Scenario compilation

`core/scenario_compiler.py` converts the Supported Domain into required obligations.

The compiler does not need to generate a naive Cartesian product of every factor. Rules should be compiled over the factors that can actually affect them.

Conceptually:

```text
rule
+ factor dependencies
+ boundaries / relevant classes
+ state-transition requirements
        ↓
required obligations
```

Every required obligation needs a stable scenario identity. That identity is later used for traceability and evidence reconstruction.

The compiler is therefore part of the trusted claim boundary: an incomplete compiler can make a verifier look green simply by failing to require important cases.

---

## 6. Step 3 — Browser replay

`core/replay_engine.py` is the canonical browser measurement primitive for the bundled proof path.

Its responsibilities include:

1. create the correct Playwright browser context;
2. navigate to the required route;
3. establish the required UI state;
4. run Measurement Readiness;
5. extract rendered information;
6. execute applicable verification rules;
7. execute required transitions;
8. record results under the exact compiled scenario;
9. attach rendered-environment identity;
10. add evidence to the Evidence DAG.

The replay engine must not fabricate a `PASS` when a state cannot be established or a checker cannot produce a result.

The correct fallback is `UNKNOWN`.

---

## 7. Step 4 — Measurement Readiness

A rendered measurement is only meaningful when the page is ready to be measured.

`core/coverage.py` contains the current readiness machinery used by the bundled pipeline.

The readiness model exists to prevent errors such as:

```text
page.goto()
wait arbitrary timeout
measure unstable layout
call it PASS
```

Depending on the rule and domain, readiness can require evidence about:

- document/application readiness;
- font resolution;
- image/asset state;
- hydration;
- geometry stability;
- controlled animation or timing conditions.

If required readiness cannot be established, the rendered proof is `UNKNOWN`.

---

## 8. Step 5 — Geometry extraction and checks

The Geometric Visual Harness lives under `gvh/`.

The browser is the forward simulator. GVH measures the browser output; it does not attempt to replace CSS layout with a second layout engine.

The geometry path includes concepts such as:

```text
viewport
nodes / elements
boxes
fragments
relative geometry
containment
spacing
alignment
collision
clipping
stacking / occlusion signals
responsive relationships
```

The full architectural target is documented in `docs/03-geometric-visual-harness.md`. The implementation-status document states which precision levels are currently executable.

---

## 9. Step 6 — Five verification layers

UI-Agentic keeps five concerns distinct:

```text
GEOMETRY
PAINT
INTERACTION
ACCESSIBILITY / SEMANTICS
TEMPORAL / ENVIRONMENTAL
```

This separation is important because a success in one layer cannot prove another.

Examples:

- correct geometry does not prove keyboard operability;
- a correct role does not prove the control is visible;
- a screenshot does not prove focus containment;
- stable source code does not prove runtime fonts loaded correctly.

Cross-layer contracts combine evidence only when the user-facing invariant genuinely spans multiple layers.

Current reference examples include:

```text
TARGET_OPERABLE
FOCUS_USABLE
MODAL_INTEGRITY
```

---

## 10. Step 7 — Coverage Ledger

The Coverage Ledger records whether the required obligations were actually closed.

The important distinction is:

```text
required
≠ tested
≠ passed
```

A useful summary contains at least:

```text
required
tested
passed
failed
unknown
```

The final confirmation path requires all required obligations to be represented and no required `FAIL` or `UNKNOWN` to remain.

Coverage is not an aesthetic score.

---

## 11. Step 8 — Evidence DAG

Evidence is content-addressed so that it can be reused only when its declared inputs remain compatible.

Conceptually an evidence key binds:

```text
subject / code identity
contract identity
rule
scenario
browser / platform
rendered environment
measurement kernel / checker identity
readiness inputs
```

The exact implementation may evolve, but the invariant does not:

> Evidence from one incompatible subject, contract, scenario, verifier, or environment must not silently satisfy another.

The Evidence DAG enables dependency-aware regression. When an input changes, dependent evidence becomes stale; unaffected evidence can remain valid when its full identity still matches.

---

## 12. Step 9 — Proof levels

A rule declares the minimum proof strength it requires.

```text
OBSERVED
BOUNDED
CERTIFIED
```

### OBSERVED

A direct measurement of one declared rendered case.

### BOUNDED

A demonstrated bound over a declared region of the domain.

### CERTIFIED

A property established by an applicable certification method whose certificate can be checked independently.

Sampling does not become `BOUNDED` merely by increasing sample count. A model-generated assertion does not become `CERTIFIED` because the model is confident.

---

## 13. Step 10 — Mutation and verifier adequacy

A verifier can be wrong even when the application is correct.

UI-Agentic therefore tests selected critical failure modes by injecting faults and requiring the verifier to detect them.

The expected loop is:

```text
baseline PASS
→ inject defect
→ target rule becomes FAIL or UNKNOWN
→ revert defect
→ baseline PASS
```

A surviving critical mutant means the verifier has a blind spot.

Mutation adequacy does not prove all possible rules are complete. It provides evidence that declared critical failure modes are actually detectable.

---

## 14. Step 11 — Visual Acceptance

Not all visual quality is reducible to a deterministic geometric or pixel rule.

UI-Agentic therefore keeps a separate Visual Acceptance layer.

A visual review should bind:

```text
required screenshot/state matrix
exact current-run image identity
review-equivalence identity when explicitly defined
reviewer identity
review metadata
rubric
verdict
```

The verdict is:

```text
ACCEPTED
REJECTED
UNKNOWN
```

Visual review is rubric evidence. It never becomes a mathematical certificate simply because a reviewer accepted it.

---

## 15. Step 12 — Independent gates

The scripts under `scripts/` exist partly to avoid trusting one large runner with every claim.

Important responsibilities include:

- build current-run evidence;
- build record-bound traceability;
- verify required proof levels;
- verify mutation adequacy;
- capture and verify runtime identity;
- enforce visual review scope;
- run provenance tamper tests;
- verify pre-attestation closure;
- finalize the attestation;
- independently re-check provenance and trusted-kernel identity.

The exact filenames can evolve. The architectural principle is more important:

> A final claim should be reconstructed and checked by small deterministic gates rather than accepted because one generator wrote `true` into a report.

---

## 16. Step 13 — Trusted Verification Kernel

The Trusted Verification Kernel is the minimal code and configuration whose correctness the final claim ultimately depends on.

It includes critical checkers and decision logic, not every repository file.

`core/trust_kernel.py` maintains the current content-addressed kernel identity used by the reference attestation path.

If trusted decision code changes, the trusted-kernel digest changes and previous attestations cannot silently represent the new verifier.

---

## 17. Step 14 — Runtime identity

A proof can depend on runtime details beyond source code.

The reference pipeline records runtime identity for relevant components such as:

- the Python executable;
- Playwright version;
- the browser binary actually launched;
- selected font identities;
- the execution environment.

This matters because two runs with identical source can render differently under incompatible runtime inputs.

Runtime identity is part of provenance, not an optimization detail.

---

## 18. Step 15 — Final Confirmation Gate

The Final Confirmation Gate is a conjunction of required conditions, not a weighted score.

Conceptually:

```text
coverage closed
AND traceability closed
AND proof levels satisfied
AND required certificates valid
AND readiness satisfied
AND critical mutants survived = 0
AND assumptions explicit
AND regression closed
AND parent contracts respected
AND required transitions closed
AND cross-layer invariants closed
AND required compliance obligations closed
AND visual acceptance = ACCEPTED
```

One missing required gate blocks confirmation.

A high score cannot compensate for a hard failure.

---

## 19. Step 16 — Verification Attestation

The final attestation is a content-addressed statement about an identified snapshot.

The reference CI path binds information such as:

```text
subject / build identity
contract identity
scenario set
rules / checker identity
measurement kernel
trusted verification kernel
environment manifest
runtime identity
Evidence DAG root
report root
visual evidence root
final gate
source run
```

The attestation is not a permanent repository status.

When a relevant input changes, the previous attestation remains a historical statement about the old snapshot.

---

## 20. Step 17 — `LOCKED`

`LOCKED` means:

> This identified snapshot satisfied the declared confirmation contract using the bound proof bundle and trusted verification inputs.

It does **not** mean:

- the repository can never change;
- every possible browser/environment is covered;
- the architecture is universally complete;
- subjective aesthetics were mathematically certified;
- future commits inherit the verdict.

Locked means controlled change.

---

## 21. External-project path

The `ui_agentic/` package is the productization layer for verifying another application.

The current external flow is intentionally narrower than the fully closed bundled reference path.

Conceptually:

```text
external project
      ↓
.ui-agentic contract
      ↓
HTTP adapter
      ↓
scenario compilation
      ↓
canonical replay engine
      ↓
external verification report
```

The external `lock` command remains fail-closed until the entire external subject / contract / verifier / evidence / visual / runtime chain is authoritative.

See `docs/05-project-status-and-roadmap.md` and `docs/06-using-ui-agentic.md` for the exact current boundary.

---

## 22. How to audit a code change

When reviewing a change, ask in this order:

1. **What public claim changes?**
2. **Which Supported Domain factors can it affect?**
3. **Which rules or scenario compilation paths depend on it?**
4. **Does the change affect browser measurement or only reporting?**
5. **Does it change evidence identity?**
6. **Does it change the Trusted Verification Kernel?**
7. **Does a critical failure mode need a new mutant?**
8. **Does the same triggering rule get revalidated?**
9. **Which prior evidence becomes stale?**
10. **Do public docs and status labels remain accurate?**

This review order prevents apparently small implementation changes from silently expanding or weakening the verification claim.

---

## 23. Where to go next

- For the complete methodology: `docs/00-project-guide.md`
- For hierarchy and ownership: `docs/01-pyramidal-stabilization.md`
- For orchestration and verification: `docs/02-agent-architecture-and-verification.md`
- For geometry: `docs/03-geometric-visual-harness.md`
- For proof and attestation: `docs/04-proof-evidence-attestation.md`
- For current capability boundaries: `docs/05-project-status-and-roadmap.md`
- For CLI usage: `docs/06-using-ui-agentic.md`
- For adding new behavior safely: `docs/08-extending-ui-agentic.md`
- For common questions: `docs/09-faq.md`
