# UI-Agentic Documentation

This directory is the public documentation hub for UI-Agentic.

The documentation is organized in layers so readers do not need to start with the most technical material.

---

## Start here

### New to UI-Agentic

Read these in order:

1. [`../README.md`](../README.md) — what the project is, why it exists, and what it currently does.
2. [`00-project-guide.md`](00-project-guide.md) — the complete A-to-Z explanation of the architecture and workflow.
3. [`GLOSSARY.md`](GLOSSARY.md) — precise definitions for project terminology.
4. [`05-project-status-and-roadmap.md`](05-project-status-and-roadmap.md) — what is implemented, reference-only, partial, or planned.

This path is designed for users, reviewers, and contributors who need a correct mental model before reading the specifications.

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

## Documentation by task

### I want to understand the project quickly

```text
README
  ↓
00 Project Guide
  ↓
Glossary
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

### I want to work on verification evidence or gates

```text
02 Agent Architecture & Verification
  ↓
04 Proof / Evidence / Attestation
  ↓
../core/
  ↓
../scripts/
  ↓
../tests/
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

Start with the root README quick start and then inspect:

- `../ui_agentic/` — CLI and external application adapter;
- `../supported-domain.yaml` — reference domain model;
- `../references/supported-domain.md` — operational domain guidance;
- `05-project-status-and-roadmap.md` — current external-project limitations.

---

## Focused operational references

The `../references/` directory contains narrower documents used by the workflow and verification layers. These are intended to support implementation and agent routing without duplicating the core specifications.

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

---

## Rules and executable behavior

The documentation describes the intended architecture. It is not a substitute for the executable implementation.

For a specific commit or release, the auditable behavior comes from:

```text
core/
gvh/
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
- [`../SKILL.md`](../SKILL.md) — agent workflow/routing contract.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution requirements.
- [`../SECURITY.md`](../SECURITY.md) — vulnerability reporting policy.
- [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) — community conduct policy.
- [`../LICENSE`](../LICENSE) — MIT License.

---

## Documentation quality rule

Public documentation should always distinguish these four statements:

```text
WHAT THE ARCHITECTURE REQUIRES
WHAT THE CURRENT REFERENCE IMPLEMENTATION DEMONSTRATES
WHAT THE EXTERNAL CLI CURRENTLY SUPPORTS
WHAT REMAINS PLANNED OR PARTIAL
```

Do not convert an architectural target into a marketing claim, and do not describe a narrow reference implementation as universal product coverage.
