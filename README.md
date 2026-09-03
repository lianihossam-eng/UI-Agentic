# UI-Agentic

UI-Agentic is an evidence-driven system for designing, stabilizing, verifying, and controlling changes to user interfaces.

It combines a **pyramidal stabilization method**, a **browser-based verification architecture**, and a **Geometric Visual Harness (GVH)** under one canonical workflow.

The core idea is simple:

```text
GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL
```

A lower level must never solve a local problem by silently destabilizing a higher-level contract.

UI-Agentic is not a visual-score generator, a screenshot linter, or a single design prompt. It is a stateful verification system built around explicit support contracts, deterministic evidence, fail-closed gates, controlled regression, and snapshot-bound attestations.

---

## Why UI-Agentic exists

UI work often fails in one of two ways:

1. teams optimize isolated screens while the global system drifts; or
2. automated checks produce reassuring scores without proving that the declared product surface is actually covered.

UI-Agentic addresses both problems.

It first defines **what the product claims to support**, then compiles that contract into required verification obligations. It stabilizes the interface from the top of the hierarchy downward, measures rendered behavior in the browser, records evidence, revalidates the exact rule that triggered a change, and invalidates only the proofs affected by later changes.

The result is a workflow where a final `LOCKED` verdict means:

> This identified UI snapshot satisfied the declared support contract, required verification obligations, proof requirements, regression gates, and visual acceptance contract under the attested environment.

It never means “this UI is correct in every imaginable environment.”

---

## The three core specifications

The project is organized around three independent responsibilities.

| Specification | Responsibility |
| --- | --- |
| [01 — Pyramidal UI Stabilization System](docs/01-pyramidal-stabilization.md) | Work order, ownership, stabilization states, change boundaries, escalation, and regression. |
| [02 — UI Agent Architecture & Verification](docs/02-agent-architecture-and-verification.md) | Orchestration, Supported Domain, Scenario Compiler, proof model, evidence, gates, and verification layers. |
| [03 — Geometric Visual Harness](docs/03-geometric-visual-harness.md) | Objective geometry extraction, spatial constraints, responsive boundaries, occlusion, stability margins, and geometric regression. |

Additional public documentation:

- [Proof, Evidence, and Attestation Model](docs/04-proof-evidence-attestation.md)
- [Current Implementation Status and Roadmap](docs/05-project-status-and-roadmap.md)

---

## Canonical workflow: A to Z

```text
0. DECLARE SUPPORTED DOMAIN
   ↓
1. DISCOVER PRODUCT
   ↓
2. ESTABLISH / EXTRACT GLOBAL DESIGN CONTRACT
   ↓
3. STABILIZE GLOBAL
   ↓
4. STABILIZE FAMILIES
   ↓
5. STABILIZE PAGE STRUCTURES
   ↓
6. STABILIZE SECTIONS / COMPONENTS / STATES
   ↓
7. RUN FIVE-LAYER VERIFICATION
   ↓
8. CLASSIFY FINDINGS + OWNER + EVIDENCE
   ↓
9. DIAGNOSE ROOT CAUSE
   ↓
10. FIX AT LOWEST VALID OWNER
   ↓
11. REVALIDATE THE SAME RULE
   ↓
12. RUN DEPENDENCY-AWARE REGRESSION
   ↓
13. CLOSE COVERAGE
   ↓
14. RUN VISUAL ACCEPTANCE REVIEW
   ↓
15. FINAL CONFIRMATION GATE
   ↓
16. EMIT VERIFICATION ATTESTATION
   ↓
17. LOCK
```

The order matters. UI-Agentic intentionally prevents detail-level polish from bypassing structural instability, failed interactions, accessibility blockers, or missing evidence.

---

## Supported Domain

UI-Agentic does not define `100%` as an unbounded claim.

Before final verification, the project declares a Supported Domain:

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

That domain is compiled into a Required Scenario Set:

```text
R = Compile(
  Dₛ,
  rules,
  dependency hypergraph,
  contracts,
  boundaries
)
```

The compiler does not blindly brute-force the full Cartesian product. Each rule is evaluated over the factors that can actually affect it. Declared independence must be justified; unknown interactions remain part of robustness discovery and may block stronger proof claims.

Therefore:

> **100% confirmed = 100% of the required obligations derived from the declared Supported Domain, with every required proof level satisfied.**

Anything outside that contract is outside the claim.

See [Supported Domain reference](references/supported-domain.md).

---

## Pyramidal stabilization

The ownership hierarchy is:

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

Examples of ownership:

| Level | Typical ownership |
| --- | --- |
| Global | typography scale, semantic colors, spacing scale, radii, elevation, responsive philosophy |
| Family | application shell, navigation, shared headers, common containers |
| Page | macro layout, information hierarchy, page-specific density, page state architecture |
| Section | internal grid, toolbar structure, relationships between blocks |
| Component | anatomy, internal spacing, variants, control dimensions |
| State | loading, empty, error, selected, disabled, modal-open, transition behavior |
| Detail | optical alignment, micro-spacing, fine visual polish |

### Fundamental invariant

> Constraints flow downward. Change requests escalate upward. Regression flows downward again.

A component should not invent a local breakpoint to compensate for a page-level layout problem. A page should not redefine the global spacing system to repair one section. Every fix must be applied at the **lowest valid owner** that can solve the root cause without violating its parent contract.

---

## Stabilization states

UI-Agentic models progress explicitly:

```text
UNEXPLORED
→ DRAFT
→ STRUCTURED
→ STABLE
→ VERIFIED
→ LOCKED
```

- **STRUCTURED** — architecture is defined but still freely changeable.
- **STABLE** — reliable enough to allow work to proceed to the next lower level.
- **VERIFIED** — applicable verification obligations have passed with required evidence.
- **LOCKED** — the state is attested; further changes require impact analysis and controlled revalidation.

`LOCKED` means **controlled change**, not immutability.

---

## Five verification layers

UI-Agentic keeps verification concerns separate so that one kind of success cannot hide another kind of failure.

| Layer | What it verifies |
| --- | --- |
| **Geometry** | position, dimensions, grouping, spacing, containment, clipping, responsive boundaries, layering, occlusion |
| **Paint** | rendered typography, color, contrast, borders, shadows, opacity, masks, raster fidelity |
| **Interaction** | hit testing, pointer/touch behavior, keyboard behavior, focus, scrolling, state transitions |
| **Accessibility / Semantics** | roles, names, reading order, focus order, ARIA/state semantics, reduced motion |
| **Temporal / Environmental** | fonts, images, hydration, async states, virtualization, time, browser/environment identity, layout stability |

The GVH owns the geometry layer. The UI-Agentic orchestrator coordinates all five.

### Cross-layer invariants

Some failures cannot be validated correctly by one layer in isolation. UI-Agentic therefore supports composite contracts such as:

```text
FOCUS_USABLE
TARGET_OPERABLE
MODAL_INTEGRITY
VISUAL_SEMANTIC_ORDER
ASYNC_STABILITY
```

For example, a button can have a valid DOM role and acceptable size but still be unusable because another element intercepts the hit test. A modal can be visually centered while keyboard focus escapes into the background. Composite invariants require one atomic evidence bundle across the relevant layers.

---

## Proof levels

Every verification rule declares a minimum proof level:

```text
OBSERVED
  Direct measurement of a rendered case.

BOUNDED
  A demonstrated bound over a declared region of the domain.

CERTIFIED
  A property demonstrated over the declared domain by an applicable
  certification method and independently checked.
```

A collection of samples does not automatically become a bound. A screenshot matrix does not automatically become a certificate.

The system fails closed:

```text
real positive evidence       → PASS
real negative evidence       → FAIL
missing/invalid evidence     → UNKNOWN
required UNKNOWN             → blocks confirmation
```

---

## Trusted Verification Kernel

Evidence generators are not trusted simply because they produced a result.

Agents, solvers, search procedures, fuzzers, and numerical methods are treated as untrusted evidence producers by default. Strong proof claims must be independently checkable.

The intended trust bundle is:

```text
contract
+ evidence or certificate
+ small deterministic checker
+ explicit assumptions
```

A certificate that cannot be independently checked is not accepted as `CERTIFIED`.

---

## Measurement readiness

Rendered verification is meaningful only when the UI is ready to be measured.

The Measurement Readiness Gate can include:

- deterministic fixtures and network state;
- expected application state reached;
- fonts resolved;
- required assets resolved or intentionally failed;
- hydration and async work completed as declared;
- controlled time, locale, randomness, and environment when relevant;
- geometry stable for the declared observation window;
- animations completed, neutralized, or explicitly tested.

A fixed sleep is not evidence of readiness.

If readiness cannot be established, rendered obligations become `UNKNOWN` rather than receiving a synthetic pass.

---

## Evidence DAG and targeted regression

Verification evidence is content-addressed.

Conceptually, an evidence key binds:

```text
hash(
  code / subject identity
+ contract
+ rule
+ scenario
+ browser and platform
+ fonts and assets
+ locale and DPR
+ verifier/checker identity
)
```

When an input changes, only dependent evidence becomes stale. This enables targeted regression instead of unconditional full reruns while still preventing stale proofs from being reused across incompatible snapshots.

---

## Visual acceptance

Not every quality criterion can be converted into a formal geometric or semantic rule.

UI-Agentic therefore keeps subjective visual judgment explicit through a **Visual Acceptance Contract**. The review can cover:

- hierarchy;
- composition;
- perceived typography;
- density and whitespace;
- coherence;
- brand and imagery;
- comparison against accepted references or exemplars;
- named disqualifiers.

The verdict is:

```text
ACCEPTED | REJECTED | UNKNOWN
```

Visual acceptance is rubric evidence. It is never promoted to a formal certificate.

---

## Final confirmation gate

A UI snapshot may be confirmed only when the required closure conditions are satisfied, including:

```text
Coverage = 100% of required obligations
Requirement/failure-mode traceability = complete
Required proof levels = satisfied
Certificate/checker validation = complete where required
Measurement readiness = satisfied
Critical verification mutants survived = 0
Unstated proof assumptions = 0
Hard FAIL = 0
Required UNKNOWN = 0
Open regression = 0
Unrevalidated fixes = 0
Parent contract violations = 0
Required state/transition obligations = complete
Required cross-layer invariants = complete
Declared compliance obligations = complete
Critical geometry/paint failures = 0
Critical temporal/environmental instability = 0
Visual Acceptance Contract = ACCEPTED
```

No aggregate quality score is allowed to mask a hard failure.

---

## Verification attestation and `LOCKED`

`LOCKED` is not a permanent boolean stored independently of its evidence.

The authoritative result is a **Verification Attestation** bound to the exact verified snapshot. The attestation can include digests for:

```text
subject/build
contract
scenario set
rules/checkers
measurement kernel
trusted verification kernel
environment manifest
runtime identity
evidence DAG root
report root
visual evidence root
final gate
```

Any relevant input change makes the affected evidence stale and requires impact analysis and revalidation before another `LOCKED` attestation can be issued.

See [Proof, Evidence, and Attestation Model](docs/04-proof-evidence-attestation.md).

---

## Repository structure

```text
UI-Agentic/
├── README.md                     # public entry point
├── SKILL.md                      # agent routing contract
├── supported-domain.yaml         # executable reference Supported Domain
├── ui_agentic/                   # external-project CLI and adapters
├── core/                         # scenario, coverage, evidence, replay, trust
├── gvh/                          # geometric extraction and verification
├── rules/                        # rule definitions
├── references/                   # focused operational references
├── docs/                         # complete public architecture documentation
├── scripts/                      # proof and CI verification gates
├── assets/templates/             # reference vertical-slice pages
├── evaluations/                  # evaluation fixtures
├── tests/                        # verifier tests
├── reports/                      # checked-in review inputs/reference data only
├── archive/                      # historical experiments; not normative
└── .github/workflows/            # fail-closed proof pipeline
```

### Normative vs historical content

The current public source of truth is:

```text
README.md
+ docs/
+ SKILL.md
+ references/
+ rules/
+ supported-domain.yaml
+ executable verifier code
```

Files under `archive/` are historical experiments retained for traceability. They are **not** part of the current architecture or public API.

---

## Quick start: reference implementation

### Requirements

- Python 3.10+
- Playwright
- Chromium managed by Playwright

### Install for local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
playwright install chromium
```

On Windows PowerShell, activate the virtual environment with the appropriate Windows activation command instead of `source`.

### Run the bundled reference verifier

```bash
python run_goal_verify.py
```

The repository CI performs substantially more than this single command. The authoritative reference attestation is produced only by the complete fail-closed GitHub Actions proof pipeline.

---

## Using UI-Agentic against another local application

The public CLI introduced in the current productization work is intentionally conservative.

Initialize a contract:

```bash
ui-agentic init --project . --base-url http://127.0.0.1:3000
```

Inspect declared routes:

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

Attempt the lock gate:

```bash
ui-agentic lock --project .
```

### Important status note

External-project verification is being generalized incrementally. The current public CLI can execute browser obligations against an HTTP application, but **external-project `LOCKED` attestation is intentionally fail-closed until the external subject, contract, verifier, evidence DAG, visual review, and runtime provenance are all bound by the same authoritative model**.

The bundled reference implementation has a stricter CI attestation path than the current external-project CLI.

For an exact capability matrix, see [Current Implementation Status and Roadmap](docs/05-project-status-and-roadmap.md).

---

## What UI-Agentic does not claim

UI-Agentic does **not** currently claim:

- universal correctness for arbitrary UIs;
- complete WCAG 2.2 AA conformance for every application;
- complete ACT Rules coverage;
- multi-browser certification by default;
- continuous responsive-domain certification for every rule;
- internal geometry certification for opaque canvas/WebGL/cross-origin surfaces without instrumentation;
- automatic proof that subjective design intent is “good.”

Every claim must remain bounded by the declared contract and available proof.

---

## Current reference implementation

The repository includes a deliberately narrow executable vertical slice used to test the verification architecture itself. It exercises multiple routes, responsive widths, modal states and transitions, cross-layer rules, mutation/fault injection, provenance tamper checks, visual review, and attestation generation.

The exact obligation count, mutation set, browser identity, evidence roots, and attestation digest are runtime facts produced by CI rather than permanent marketing claims in this README.

This prevents documentation from becoming stale whenever the compiler or verifier evolves.

---

## Development principles

The project follows these non-negotiable rules:

1. Top-down constraints.
2. Breadth before depth.
3. Lowest valid owner.
4. Upward escalation only when necessary.
5. Downward regression after parent changes.
6. Evidence before `FAIL`.
7. Required `UNKNOWN` blocks confirmation.
8. A fix must revalidate the same triggering rule.
9. Geometry, paint, interaction, semantics, and time remain distinct verification concerns.
10. No silent local patching.
11. No aggregate score may mask hard failures.
12. Sampling alone never becomes a stronger proof level by repetition.
13. Cached evidence is reusable only when its declared inputs remain compatible.
14. Significant interactive flows are verified as transitions, not only isolated states.
15. Visual quality is accepted against an explicit visual contract.
16. `LOCKED` always refers to an identified snapshot and evidence bundle.

---

## Documentation map

Start here depending on what you want to understand:

| Goal | Document |
| --- | --- |
| Understand the project in five minutes | `README.md` |
| Understand stabilization order and ownership | [`docs/01-pyramidal-stabilization.md`](docs/01-pyramidal-stabilization.md) |
| Understand orchestration and verification architecture | [`docs/02-agent-architecture-and-verification.md`](docs/02-agent-architecture-and-verification.md) |
| Understand the geometry engine | [`docs/03-geometric-visual-harness.md`](docs/03-geometric-visual-harness.md) |
| Understand proofs, evidence, gates, and lock semantics | [`docs/04-proof-evidence-attestation.md`](docs/04-proof-evidence-attestation.md) |
| Understand what is implemented today | [`docs/05-project-status-and-roadmap.md`](docs/05-project-status-and-roadmap.md) |
| Use UI-Agentic as an agent skill | [`SKILL.md`](SKILL.md) |
| Contribute | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Report a security issue | [`SECURITY.md`](SECURITY.md) |

---

## Contributing

Contributions are welcome when they preserve the verification model and fail-closed behavior.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

For significant verifier changes, include:

- the affected Supported Domain or contract;
- the rule/failure mode being changed;
- tests for the positive path;
- at least one relevant negative or mutation case when applicable;
- evidence that the exact triggering rule is revalidated;
- regression impact notes.

---

## Security

Please do not disclose vulnerabilities through a public issue. Follow the process in [SECURITY.md](SECURITY.md).

---

## License

UI-Agentic is released under the [MIT License](LICENSE).
