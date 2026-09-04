# 05 — Current Implementation Status and Roadmap

This document separates **implemented public behavior** from **architectural target behavior**.

UI-Agentic is intentionally conservative about claims. A concept described in the architecture is not automatically considered implemented, and an implemented reference capability is not automatically generalized to arbitrary external projects.

---

## 1. Status categories

The documentation uses the following categories:

```text
IMPLEMENTED
  Executable in the public repository.

REFERENCE IMPLEMENTATION
  Implemented and exercised by the bundled vertical slice, but not necessarily
  generalized to arbitrary external projects.

PARTIAL
  A meaningful subset exists, but the architectural target is broader.

PLANNED
  Defined by the architecture but not yet implemented as a complete public path.
```

---

## 2. Public repository status

At the time of this documentation overhaul, the stable `main` branch contains:

- the canonical scenario compiler;
- browser replay through Playwright/Chromium;
- a fail-closed Coverage Ledger;
- content-addressed evidence generation;
- Measurement Readiness checks;
- rule/failure-mode traceability infrastructure;
- mutation/fault-injection gates;
- runtime and environment identity checks;
- visual evidence and visual acceptance gates;
- Trusted Verification Kernel checks;
- final CI attestation for the bundled reference implementation;
- an external-project CLI with HTTP application adapter support.

The exact number of obligations, mutants, evidence records, and current browser/runtime versions are runtime facts produced by CI. They are deliberately not hard-coded into the public project description.

---

## 3. Bundled reference vertical slice

The repository includes a deliberately narrow application surface used to prove the verification architecture itself.

The reference surface includes multiple routes, responsive viewport widths, modal states/transitions, keyboard/mouse behavior, cross-layer rules, visual evidence, mutation testing, provenance tamper tests, and final attestation.

This reference implementation exists to answer a specific question:

> Can the architecture close a declared Supported Domain with deterministic, fail-closed evidence and independently checked gates?

It is not presented as a universal UI benchmark.

---

## 4. Five-layer implementation status

### Geometry — IMPLEMENTED / REFERENCE IMPLEMENTATION

Current public code can measure and verify a meaningful set of geometric properties through the browser and GVH components.

The full architectural target is broader and includes higher-precision transformed/clipped regions, continuous responsive proofs, stronger layer/occlusion modeling, sensitivity, and stability-margin analysis.

### Paint — PARTIAL

The public verifier includes rendered paint checks such as contrast-related verification and screenshot identity/review infrastructure.

The full target includes richer style lineage, hermetic raster fidelity, region-aware diagnostics, and explicitly contracted perceptual methods.

### Interaction — IMPLEMENTED / REFERENCE IMPLEMENTATION

The reference path executes real browser actions and verifies interaction-related properties including hit testing and modal behavior.

The target includes broader pointer/touch/gesture/state-machine coverage across arbitrary applications.

### Accessibility / Semantics — PARTIAL

Keyboard/focus-related checks and composite focus usability exist in the reference implementation.

The project does not claim complete WCAG 2.2 AA or ACT Rules coverage for arbitrary applications.

### Temporal / Environmental — PARTIAL

The verifier includes measurement readiness, geometry stability checks, runtime identity, font/environment binding, and async-related failure injection in the reference pipeline.

The full architecture includes broader animation, virtualization, dynamic viewport, mobile keyboard, locale, browser/platform, and async state exploration.

---

## 5. Cross-layer invariants

The reference implementation currently exercises composite invariants such as:

```text
TARGET_OPERABLE
FOCUS_USABLE
MODAL_INTEGRITY
```

Architectural targets additionally include:

```text
VISUAL_SEMANTIC_ORDER
ASYNC_STABILITY
```

Composite invariants remain important because a one-layer pass cannot establish end-user operability by itself.

---

## 6. Proof-level status

### OBSERVED — IMPLEMENTED

Direct rendered measurement is the primary executable proof level today.

### BOUNDED — INFRASTRUCTURE EXISTS / BROADER METHODS PLANNED

The project has certificate/checker concepts and refuses to promote raw sampling into `BOUNDED` proof.

Broader interval, enclosure, continuous-domain, and adaptive-bound methods are part of the target architecture.

### CERTIFIED — KERNEL MODEL IMPLEMENTED / DOMAIN-SPECIFIC CERTIFICATION PARTIAL

The Trusted Verification Kernel and independent-checker principle are implemented as an architectural and CI trust boundary.

General certification methods depend on the property being proven and remain an area of expansion.

---

## 7. Visual acceptance status

The bundled reference path includes an explicit visual contract and screenshot matrix.

Current visual verification distinguishes:

- exact current-run screenshot identity;
- deterministic review fingerprinting where bounded raster-equivalence reuse is allowed;
- explicit reviewer identity and review metadata;
- final `ACCEPTED | REJECTED | UNKNOWN` status.

Visual acceptance remains rubric evidence. It is not promoted to a formal certificate.

---

## 8. Internal/reference attestation status

The bundled reference implementation has an authoritative CI attestation path.

The complete pipeline includes, conceptually:

```text
unit tests
→ fault injection
→ current-run browser evidence
→ traceability / proof-level gates
→ runtime identity
→ complete visual contract
→ final goal verification
→ provenance tamper tests
→ pre-attestation gates
→ attestation finalization
→ strict provenance / kernel checks
→ LOCKED assertion
→ CI artifact
```

The authoritative attestation is generated for the exact CI run/commit rather than committed as a static file that would create a recursive commit-binding problem.

---

## 9. External-project CLI status

The public CLI currently exposes:

```text
ui-agentic init
ui-agentic discover
ui-agentic verify
ui-agentic report
ui-agentic lock
```

### `init` — IMPLEMENTED

Creates an external-project verification contract.

### `discover` — IMPLEMENTED

Probes declared HTTP routes and records basic rendered facts.

### `verify` — IMPLEMENTED / EARLY PRODUCTIZATION

Compiles the declared domain and executes browser obligations against a running HTTP application using the canonical replay engine.

### `report` — IMPLEMENTED

Prints the latest external verification summary.

### `lock` — DELIBERATELY FAIL-CLOSED

The command exists, but the current stable public version refuses to emit an authoritative external `LOCKED` verdict.

This is intentional.

A trustworthy external lock must bind all of the following in one model:

```text
external subject identity
external contract identity
verifier identity
Evidence DAG entries
visual review identity
runtime/environment identity
final gate
attestation provenance
```

Until that model is complete, `NO LOCK` is the correct behavior.

---

## 10. Productization work in progress

The next productization stages are:

### Stage A — External identity separation

Separate:

```text
SUBJECT
CONTRACT
VERIFIER
```

so an external application is not confused with the UI-Agentic repository commit.

### Stage B — Contract-bound external Evidence DAG

Every external evidence key must bind the external verification contract and subject identity.

### Stage C — External visual review provenance

Visual approval must bind the exact external subject/contract/verifier and the complete required state matrix.

### Stage D — Distributed verifier/runtime provenance

An installed verifier must have an authoritative content identity, and runtime binaries/environment must be bound to the proof bundle.

### Stage E — Authoritative external attestation

Only after A–D can `ui-agentic lock` legitimately emit an external-project `LOCKED` attestation.

---

## 11. Architectural expansion roadmap

Beyond productization, the architecture targets:

- richer page-family and hierarchy discovery;
- stronger Design IR extraction;
- more complete geometry scene/layer modeling;
- continuous responsive-domain analysis;
- content-boundary and property-based discovery;
- richer touch and gesture support;
- broader accessibility semantics;
- explicit compliance-profile compilation;
- multi-browser/platform support;
- stronger temporal/async verification;
- opaque-surface adapters for canvas/WebGL and other non-DOM internals;
- better root-cause diagnosis and minimal conflict extraction;
- more general bounded/certified proof methods;
- reusable external-project CI integration.

---

## 12. Explicit non-claims

The current project does not claim:

- universal UI correctness;
- complete accessibility conformance for arbitrary products;
- complete browser/platform coverage;
- universal continuous responsive certification;
- certified internal geometry of opaque surfaces without instrumentation;
- automatic proof of subjective design quality;
- authoritative external-project `LOCKED` status in the current stable CLI.

---

## 13. Release discipline

A public release should preserve the same evidence discipline as the verifier itself.

Before declaring a release candidate stable:

```text
clean tests
→ complete reference replay
→ mutation/fault adequacy
→ provenance/tamper gates
→ visual acceptance
→ deterministic attestation
→ final LOCKED assertion for the release snapshot
```

Documentation claims should be checked against the implementation at the same time.

---

## 14. Reading this project correctly

The repository contains both:

1. a **general architecture** for evidence-driven UI stabilization and verification; and
2. an **incrementally generalized implementation** proving that architecture in executable slices.

The documentation deliberately distinguishes those two levels.

If a capability is architectural but not yet generalized, this file should say so explicitly rather than letting the README imply that it is already universal.
