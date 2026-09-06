# UI-Agentic Documentation

This directory is the public documentation hub for UI-Agentic.

The documentation is organized by reader intent. You should not need to reverse-engineer the project from source code or read every specification before you can use or review it.

---

## Start here

### New to UI-Agentic

Read these in order:

1. [`../README.md`](../README.md) — what the project is, why it exists, and what it currently does.
2. [`00-project-guide.md`](00-project-guide.md) — the complete A-to-Z explanation of the architecture and workflow.
3. [`GLOSSARY.md`](GLOSSARY.md) — precise definitions for project terminology.
4. [`05-project-status-and-roadmap.md`](05-project-status-and-roadmap.md) — what is implemented, reference-only, partial, or planned.
5. [`09-faq.md`](09-faq.md) — common questions and claim-boundary clarifications.

This path is intended for users, reviewers, potential adopters, and contributors who need a correct mental model before reading implementation details.

---

## Core specifications

The project has three primary architectural specifications. Each owns one responsibility.

### [01 — Pyramidal UI Stabilization System](01-pyramidal-stabilization.md)

Defines **how UI work is ordered and owned**.

Topics include:

- `GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL`;
- breadth before depth;
- stabilization states;
- property ownership;
- lowest-valid-owner fixes;
- upward escalation;
- dependency-aware downward regression;
- hard versus soft constraints;
- responsive ownership;
- stabilization gates.

Read this when changing methodology, design ownership, or repair strategy.

### [02 — UI Agent Architecture & Verification](02-agent-architecture-and-verification.md)

Defines **how the system compiles, executes, records, and closes verification**.

Topics include:

- operating modes;
- Supported Domain;
- Scenario Compiler;
- dependency hypergraph;
- five verification layers;
- cross-layer invariants;
- proof levels and proof sources;
- Trusted Verification Kernel;
- findings and Diagnosis Gate;
- Coverage Ledger;
- evidence identity and reuse;
- final confirmation logic;
- evaluation strategy.

Read this when working on orchestration, scenario generation, coverage, evidence, or verification rules.

### [03 — Geometric Visual Harness](03-geometric-visual-harness.md)

Defines **how rendered UI geometry is represented and verified**.

Topics include:

- Geometry IR;
- layout boxes, fragments, transforms, clipping, and visible regions;
- coordinate chains;
- scene and layer graphs;
- spacing, alignment, containment, collision, and group constraints;
- stacking/occlusion relationships;
- stability margins;
- responsive-domain analysis;
- sensitivity and controlled perturbation;
- temporal geometry;
- geometric fingerprints and regression.

Read this when working on geometry extraction, spatial constraints, responsive boundaries, or occlusion.

---

## Trust and implementation documents

### [04 — Proof, Evidence, and Attestation Model](04-proof-evidence-attestation.md)

Defines the trust model behind a final verification claim.

It explains:

```text
OBSERVED → BOUNDED → CERTIFIED
PASS / FAIL / UNKNOWN
Evidence DAG
Measurement Readiness
Trusted Verification Kernel
runtime and environment identity
visual acceptance provenance
final confirmation gates
Verification Attestation
LOCKED
```

Read this before changing proof strength, provenance, attestations, cache reuse, or final gates.

### [05 — Implementation Status and Roadmap](05-project-status-and-roadmap.md)

Separates architecture from current executable capability.

It uses four status labels:

```text
IMPLEMENTED
REFERENCE IMPLEMENTATION
PARTIAL
PLANNED
```

Read this before interpreting a documented architectural target as something the current stable CLI universally supports.

---

## Using and maintaining the project

### [06 — Using UI-Agentic](06-using-ui-agentic.md)

The public CLI and external-project workflow:

```text
init
→ discover
→ verify
→ report
→ lock gate
```

This document also explains the current fail-closed boundary of external-project attestation.

### [07 — Codebase and Runtime Flow](07-codebase-and-runtime-flow.md)

The bridge from architecture to source code.

Read this to understand:

- what every top-level directory owns;
- how Supported Domain becomes browser evidence;
- where scenario compilation, replay, readiness, GVH, evidence, mutation, visual review, runtime identity, and attestation live;
- how the bundled reference path differs from the external-product path;
- what to inspect when auditing a change.

### [08 — Extending UI-Agentic Safely](08-extending-ui-agentic.md)

The maintainer guide for adding capabilities without weakening trust.

It covers:

- adding a rule;
- compiling required scenarios;
- checker fail-closed behavior;
- adding states and transitions;
- cross-layer invariants;
- proof and certificate methods;
- application adapters;
- browser/platform expansion;
- GVH extensions;
- visual-review changes;
- evidence identity;
- Trusted Verification Kernel changes;
- final gates;
- required testing and documentation.

### [09 — Frequently Asked Questions](09-faq.md)

Answers common questions about what UI-Agentic is, what `100% confirmed` and `LOCKED` mean, how it differs from Playwright or screenshot testing, why `UNKNOWN` exists, what is currently implemented, and what remains outside the public claim.

---

## Documentation by task

### I want to understand the project quickly

```text
README
  ↓
00 Project Guide
  ↓
Glossary / FAQ
  ↓
05 Status / Roadmap
```

### I want to understand the full methodology

```text
00 Project Guide
  ↓
01 Pyramidal Stabilization
  ↓
02 Agent Architecture & Verification
```

### I want to understand the implementation

```text
07 Codebase & Runtime Flow
  ↓
core/ + gvh/ + ui_agentic/
  ↓
scripts/ + tests/
```

### I want to work on verification evidence or gates

```text
02 Agent Architecture & Verification
  ↓
04 Proof / Evidence / Attestation
  ↓
07 Codebase & Runtime Flow
  ↓
08 Extending UI-Agentic Safely
```

### I want to work on geometry

```text
03 Geometric Visual Harness
  ↓
../gvh/
  ↓
geometry-related rules and references
```

### I want to use UI-Agentic on another application

```text
06 Using UI-Agentic
  ↓
../ui_agentic/
  ↓
../supported-domain.yaml
  ↓
05 Status / Roadmap
```

### I want to contribute a new capability

```text
CONTRIBUTING.md
  ↓
08 Extending UI-Agentic Safely
  ↓
relevant core specification
  ↓
rule / test / mutation / CI evidence
```

---

## Focused operational references

The `../references/` directory contains narrower documents used by the workflow and verification layers. These support implementation and agent routing without replacing the core specifications.

Important references include:

- global design contract;
- supported domain;
- verification stack;
- paint verification;
- interaction verification;
- accessibility verification;
- temporal/environmental verification;
- visual regression;
- anti-drift rules;
- ship readiness.

See [`../references/README.md`](../references/README.md) for the operational reference index.

---

## Rules and executable behavior

The documentation describes the intended architecture. It is not a substitute for the executable implementation.

For a specific commit or release, the auditable behavior comes from:

```text
core/
gvh/
ui_agentic/
rules/
scripts/
tests/
supported-domain.yaml
.github/workflows/
```

The implementation-status document explains where the public code is narrower than the target architecture.

---

## Source-of-truth hierarchy

Use the following interpretation order when documents and implementation details appear to differ:

```text
1. Exact executable code and CI behavior for the commit being evaluated
2. Current public contracts, rules, and Supported Domain
3. Core architecture specifications in docs/
4. Focused references
5. Historical material in archive/
```

`archive/` is explicitly non-normative. It exists for historical traceability and experimentation only.

---

## Public project files

- [`../README.md`](../README.md) — public entry point.
- [`../CHANGELOG.md`](../CHANGELOG.md) — public milestones and user-visible changes.
- [`../SKILL.md`](../SKILL.md) — agent workflow/routing contract.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution requirements.
- [`../SECURITY.md`](../SECURITY.md) — vulnerability reporting policy.
- [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) — community conduct policy.
- [`../LICENSE`](../LICENSE) — MIT License.

GitHub issue and pull-request templates are stored under `../.github/` and are designed to collect the verification scope, evidence, and trust-boundary information needed for useful review.

---

## Documentation quality rule

Public documentation must distinguish these statements:

```text
WHAT THE ARCHITECTURE REQUIRES
WHAT THE CURRENT REFERENCE IMPLEMENTATION DEMONSTRATES
WHAT THE EXTERNAL CLI CURRENTLY SUPPORTS
WHAT REMAINS PLANNED OR PARTIAL
```

Do not convert an architectural target into a marketing claim. Do not describe a narrow reference implementation as universal product coverage. Do not preserve temporary development-history language when a stable conceptual explanation is available.

All public-facing documentation should be written in clear, professional English and should define project-specific terminology before relying on it.
