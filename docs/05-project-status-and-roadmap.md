# 05 — Implementation Status and Roadmap

This document is the boundary between **the UI-Agentic architecture** and **the capabilities that are currently executable in the public repository**.

The distinction matters.

A concept can be architecturally defined without being fully implemented. A capability can be proven in the bundled reference slice without yet being generalized to arbitrary external applications.

UI-Agentic uses four status labels throughout this document:

| Status | Meaning |
| --- | --- |
| **IMPLEMENTED** | Executable behavior exists in the public repository. |
| **REFERENCE IMPLEMENTATION** | Implemented and exercised by the bundled reference slice, but not necessarily generalized to arbitrary external projects. |
| **PARTIAL** | A meaningful subset exists, but the architectural target is broader. |
| **PLANNED** | Defined by the architecture but not yet available as a complete public path. |

---

## 1. Executive status

The project currently has a mature **reference verification pipeline** and an early **external-project product surface**.

The reference pipeline already demonstrates that a declared UI domain can be compiled, measured in a real browser, checked with fail-closed rules, mutation-tested, visually reviewed, provenance-checked, and finalized into a snapshot-bound attestation.

The external-project CLI can already run browser verification against a local HTTP application, but the external attestation path remains intentionally conservative. It does not issue an authoritative external `LOCKED` verdict until all external proof identities are bound by the same trust model.

That distinction is deliberate, not a missing error check.

---

## 2. Capability matrix

| Capability | Status | Current boundary |
| --- | --- | --- |
| Pyramidal stabilization methodology | **IMPLEMENTED** as documentation / agent contract | Methodology is public and used by the project; automated enforcement is not universal for arbitrary projects. |
| Supported Domain model | **IMPLEMENTED** | Public schema/reference exists and is used by the bundled verifier. |
| Scenario Compiler | **IMPLEMENTED** | Dependency-aware compilation exists for the current rule/domain model. |
| Playwright browser replay | **IMPLEMENTED** | Chromium-based execution is the primary public path. |
| Coverage Ledger | **IMPLEMENTED** | Required/tested/pass/fail/unknown closure is enforced fail-closed. |
| Measurement Readiness | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Current checks cover the reference pipeline; the target architecture includes broader async/environmental controls. |
| Evidence DAG | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Content-addressed evidence exists; broader external-subject binding is still being generalized. |
| Rule/failure-mode traceability | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Enforced in the bundled proof pipeline. |
| Geometry verification / GVH | **IMPLEMENTED / PARTIAL** | Core geometric checks are executable; full spatial precision, continuous-domain analysis, and richer occlusion modeling remain broader targets. |
| Paint verification | **PARTIAL** | Contrast-related checks and screenshot/review identity exist; the full paint ladder is broader. |
| Interaction verification | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Real browser interaction and modal behavior are exercised in the reference slice. |
| Accessibility / semantics | **PARTIAL** | Focus/keyboard-related checks exist; no universal WCAG/ACT conformance claim is made. |
| Temporal / environmental verification | **PARTIAL** | Readiness, stability, runtime identity, and async fault classes exist; broader temporal coverage remains planned. |
| Cross-layer invariants | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | `TARGET_OPERABLE`, `FOCUS_USABLE`, and `MODAL_INTEGRITY` are exercised. |
| Mutation / fault adequacy | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Required verifier faults are injected and must be detected by CI. |
| Provenance tamper checks | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Current-run and artifact binding are tested fail-closed. |
| Visual Acceptance Contract | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Explicit visual review evidence is part of the bundled final pipeline. |
| Trusted Verification Kernel | **IMPLEMENTED / PARTIAL** | Trust-boundary and independent-checker principles are executable; general domain-specific certification remains broader. |
| Final CI attestation | **IMPLEMENTED / REFERENCE IMPLEMENTATION** | Authoritative for the bundled reference snapshot/run. |
| External HTTP app adapter | **IMPLEMENTED** | External local applications can be targeted through the public CLI. |
| External `LOCKED` attestation | **PLANNED / FAIL-CLOSED** | The command refuses to overclaim until the external proof chain is authoritative. |
| Multi-browser certification | **PLANNED** | Chromium is the current primary executable environment. |
| Universal continuous responsive certification | **PLANNED** | Architectural model exists; not a universal current capability. |
| Opaque-surface internal certification | **PLANNED / ADAPTER-DEPENDENT** | Internal canvas/WebGL/cross-origin geometry requires instrumentation. |

---

## 3. Bundled reference implementation

The repository contains a deliberately bounded reference application surface used to validate the verification architecture itself.

It includes enough variation to exercise important verifier behavior:

```text
multiple routes
responsive viewport widths
modal-open states
state transitions
keyboard and mouse behavior
cross-layer invariants
visual evidence
mutation / fault injection
provenance tamper tests
runtime identity
final attestation
```

The reference implementation answers this question:

> Can UI-Agentic close a declared Supported Domain using real browser measurements, explicit evidence, fail-closed gates, and reproducible provenance?

It is **not** presented as a universal benchmark for all web interfaces.

---

## 4. Verification-layer status

### Geometry — IMPLEMENTED / PARTIAL

Executable geometry checks exist in the public repository and are exercised through the browser and GVH components.

The broader architectural target includes:

- fragment-aware geometry;
- transformed regions;
- clipped/visible regions;
- richer stacking and occlusion modeling;
- continuous responsive-domain proofs;
- stability margins;
- sensitivity analysis;
- stronger geometric fingerprints.

### Paint — PARTIAL

Current public behavior includes selected rendered paint checks and screenshot/visual identity infrastructure.

The target paint ladder is broader:

```text
style contract
→ normative visual rules
→ hermetic raster fidelity
→ perceptual diagnostics
→ visual acceptance
```

Perceptual metrics are not treated as universal proof unless a contract explicitly defines them.

### Interaction — IMPLEMENTED / REFERENCE IMPLEMENTATION

The reference pipeline executes real browser actions and checks interaction-related behavior such as target operation, focus behavior, and modal transitions.

The generalized target includes richer:

- pointer/touch coverage;
- gesture handling;
- drag interactions;
- arbitrary application state machines;
- mobile input/environment interactions.

### Accessibility / Semantics — PARTIAL

The reference path contains keyboard/focus and composite focus-usability checks.

The project does **not** claim complete WCAG 2.2 AA conformance or complete ACT Rules coverage for arbitrary external applications.

Any future compliance claim must name the exact standard, version, level, scope, applicability model, and closed requirements.

### Temporal / Environmental — PARTIAL

Current behavior includes:

- Measurement Readiness;
- geometry stability checks;
- browser/runtime identity;
- environment binding;
- font-related identity;
- async/layout-shift failure injection.

The broader target includes more complete handling of:

- animation timelines;
- virtualization;
- lazy loading;
- dynamic viewport changes;
- mobile keyboard behavior;
- broader locale/RTL variation;
- browser/platform matrices;
- richer asynchronous state exploration.

---

## 5. Cross-layer invariants

The bundled reference implementation currently exercises composite invariants including:

```text
TARGET_OPERABLE
FOCUS_USABLE
MODAL_INTEGRITY
```

The architecture also defines broader targets such as:

```text
VISUAL_SEMANTIC_ORDER
ASYNC_STABILITY
```

These remain separate named contracts because individual layer passes cannot establish complete end-user operability.

---

## 6. Proof-level status

### OBSERVED — IMPLEMENTED

Direct rendered evidence is the primary executable proof level today.

### BOUNDED — PARTIAL

The architecture distinguishes real bounds from sampling, and the project refuses to promote repeated observations into `BOUNDED` proof without an actual bounding method.

The broader target includes interval/enclosure methods, adaptive subdivision, boundary localization, and other property-specific approaches.

### CERTIFIED — KERNEL MODEL IMPLEMENTED / DOMAIN METHODS PARTIAL

The Trusted Verification Kernel model and independent-checker discipline exist.

However, `CERTIFIED` is property-specific. There is no universal certification algorithm for every UI rule. General certification methods remain an area of expansion.

---

## 7. Visual acceptance status

The reference proof path includes an explicit visual contract and required screenshot matrix.

The model distinguishes:

```text
exact current-run screenshot identity
review identity / approved visual class
reviewer identity and metadata
ACCEPTED | REJECTED | UNKNOWN
```

Visual acceptance remains rubric evidence and never becomes a mathematical certificate merely because it was reviewed.

---

## 8. Reference attestation status

The bundled reference implementation has a strict CI attestation path.

Conceptually:

```text
unit tests
   ↓
fault injection
   ↓
current-run browser evidence
   ↓
traceability and proof-level gates
   ↓
runtime / environment identity
   ↓
complete visual contract
   ↓
final verification gate
   ↓
provenance tamper tests
   ↓
pre-attestation gates
   ↓
attestation finalization
   ↓
strict provenance and kernel checks
   ↓
LOCKED assertion
   ↓
CI artifact
```

The attestation belongs to the exact verified run/snapshot. It is not treated as a permanent repository-wide boolean.

---

## 9. External-project CLI

The stable public CLI exposes:

```text
ui-agentic init
ui-agentic discover
ui-agentic verify
ui-agentic report
ui-agentic lock
```

### `ui-agentic init` — IMPLEMENTED

Creates the external project contract/configuration.

### `ui-agentic discover` — IMPLEMENTED

Probes declared routes on a running HTTP application and records basic rendered facts.

### `ui-agentic verify` — IMPLEMENTED / EARLY PRODUCTIZATION

Compiles the external Supported Domain and runs browser obligations using the canonical replay engine.

### `ui-agentic report` — IMPLEMENTED

Displays the latest verification summary.

### `ui-agentic lock` — DELIBERATELY FAIL-CLOSED

The command exists, but the stable public external path does not yet emit an authoritative `LOCKED` attestation.

The external trust chain must ultimately bind:

```text
SUBJECT
  exact external application identity

CONTRACT
  exact external Supported Domain / verification contract

VERIFIER
  exact UI-Agentic/checker identity

EVIDENCE
  Evidence DAG entries bound to subject + contract + verifier

VISUAL REVIEW
  exact required visual scope and reviewer provenance

RUNTIME
  browser / executable / environment identity

FINAL GATE
  complete closure with no blocking FAIL/UNKNOWN

ATTESTATION
  one content-addressed statement binding all of the above
```

Until that chain is complete, `NO LOCK` is the correct behavior.

---

## 10. Productization roadmap

The productization roadmap is ordered by trust dependency rather than UI convenience.

### Stage A — External identity separation

Goal:

```text
SUBJECT ≠ CONTRACT ≠ VERIFIER
```

The external application must not be confused with the UI-Agentic repository commit.

### Stage B — Contract-bound external Evidence DAG

Every external evidence key must bind the correct external subject and verification contract.

### Stage C — External visual review provenance

Visual approval must bind the exact external subject, contract, verifier, required state matrix, and review identity.

### Stage D — Distributed verifier/runtime provenance

The installed verifier and actual runtime/browser binaries must have authoritative identities in the proof bundle.

### Stage E — Authoritative external attestation

Only after A–D are closed can external `ui-agentic lock` legitimately emit `LOCKED`.

---

## 11. Broader architecture roadmap

Beyond external-product attestation, the architecture targets:

- richer product/family discovery;
- stronger Design IR extraction;
- more complete scene/layer geometry;
- continuous responsive-domain analysis;
- content-boundary and generative discovery;
- stronger touch and gesture support;
- broader accessibility semantics;
- explicit compliance-profile compilation;
- multi-browser/platform verification;
- stronger animation/async verification;
- opaque-surface adapters;
- stronger diagnosis and conflict reduction;
- more general bounded/certified proof methods;
- reusable external-project CI integration.

---

## 12. Explicit non-claims

The current stable project does not claim:

- universal UI correctness;
- universal browser/platform coverage;
- complete accessibility standards conformance for arbitrary products;
- universal continuous responsive certification;
- certified internal geometry of opaque surfaces without instrumentation;
- automatic proof of subjective design quality;
- authoritative external-project `LOCKED` status before the external attestation chain is complete.

---

## 13. Release discipline

A public release should preserve the same evidence discipline as the verifier itself.

The expected release pattern is:

```text
clean tests
→ complete reference replay
→ mutation/fault adequacy
→ provenance/tamper gates
→ visual acceptance
→ deterministic attestation
→ final LOCKED assertion for the release snapshot
```

Documentation claims must be reviewed against executable behavior at the same time.

---

## 14. How to interpret this repository

Use this rule:

```text
Architecture documents describe the intended system.
Status documentation describes current implementation boundaries.
Executable code and CI define actual behavior for a specific commit.
```

Do not read a target architecture feature as a universal current capability, and do not generalize the bundled reference slice beyond its declared Supported Domain.
