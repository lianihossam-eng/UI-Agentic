# UI-Agentic Documentation

This directory contains the complete public architecture documentation for UI-Agentic.

## Recommended reading order

```text
README.md (repository root)
   ↓
01 — Pyramidal UI Stabilization System
   ↓
02 — UI Agent Architecture & Verification
   ↓
03 — Geometric Visual Harness
   ↓
04 — Proof, Evidence, and Attestation Model
   ↓
05 — Current Implementation Status and Roadmap
```

## Documents

### [01 — Pyramidal UI Stabilization System](01-pyramidal-stabilization.md)

Defines the work hierarchy, ownership model, stabilization states, change boundaries, escalation, and dependency-aware regression principles.

### [02 — UI Agent Architecture & Verification](02-agent-architecture-and-verification.md)

Defines modes, Supported Domain compilation, Scenario Compiler behavior, five verification layers, proof requirements, findings, ledgers, gates, and orchestration.

### [03 — Geometric Visual Harness](03-geometric-visual-harness.md)

Defines objective rendered geometry, spatial precision, scene/layer relationships, constraints, responsive boundary analysis, stability margins, and geometric regression.

### [04 — Proof, Evidence, and Attestation Model](04-proof-evidence-attestation.md)

Defines `OBSERVED / BOUNDED / CERTIFIED`, `PASS / FAIL / UNKNOWN`, evidence identity, Trusted Verification Kernel, provenance, visual review identity, final gates, and snapshot-bound `LOCKED` attestations.

### [05 — Current Implementation Status and Roadmap](05-project-status-and-roadmap.md)

Separates implemented behavior from reference-only, partial, and planned capabilities. Read this file before interpreting an architectural concept as a current universal capability.

## Other public surfaces

- [`../SKILL.md`](../SKILL.md) — agent routing contract.
- [`../references/`](../references/) — focused operational references.
- [`../rules/`](../rules/) — executable/public rule definitions.
- [`../supported-domain.yaml`](../supported-domain.yaml) — Supported Domain for the bundled reference implementation.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution requirements.
- [`../SECURITY.md`](../SECURITY.md) — private vulnerability reporting process.

## Source-of-truth rule

Architecture documentation describes the intended model. `05-project-status-and-roadmap.md` states which portions are implemented today. Executable code and CI remain the auditable source for the behavior of a specific release or commit.

Files under `../archive/` are historical and non-normative.
