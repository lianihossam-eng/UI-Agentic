---
name: ui-agentic
description: Evidence-driven UI stabilization and verification orchestrator with pyramidal ownership, five verification layers, proof levels, dependency-aware regression, and snapshot-bound attestation.
---

# UI-Agentic — Skill Router

This file is the primary routing surface for an agent using UI-Agentic.

It must **route to the smallest applicable references and rules** rather than duplicating the full architecture in one prompt.

## Canonical workflow

```text
0  DECLARE SUPPORTED DOMAIN
1  DISCOVER PRODUCT
2  ESTABLISH / EXTRACT DESIGN CONTRACT
3  STABILIZE GLOBAL
4  STABILIZE FAMILIES
5  STABILIZE PAGE STRUCTURES
6  STABILIZE SECTIONS / COMPONENTS / STATES
7  RUN FIVE-LAYER VERIFICATION
8  CLASSIFY FINDINGS + OWNER + EVIDENCE
9  DIAGNOSE ROOT CAUSE
10 FIX AT LOWEST VALID OWNER
11 REVALIDATE THE SAME RULE
12 RUN DEPENDENCY-AWARE REGRESSION
13 CLOSE COVERAGE
14 RUN VISUAL ACCEPTANCE REVIEW
15 FINAL CONFIRMATION GATE
16 EMIT VERIFICATION ATTESTATION
17 LOCK
```

See `README.md` and `docs/` for the complete public model.

## Operating modes

```text
DISCOVER | DIRECTION | BUILD | AUDIT | VERIFY | REGRESSION | POLISH
```

### Mode intent

- `DISCOVER` — map product surfaces, contracts, states, and support boundaries.
- `DIRECTION` — propose a global direction only when one is missing.
- `BUILD` — implement under existing parent contracts.
- `AUDIT` — inspect and prove without silently redesigning the product.
- `VERIFY` — execute applicable rules and produce evidence.
- `REGRESSION` — revalidate evidence invalidated by a change.
- `POLISH` — refine aesthetics after structural stability.

## Hierarchy

```text
GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL
```

Fundamental invariant:

> A lower level may not solve its local problem by silently destabilizing a higher-level contract.

## Progressive routing

| Signal | Load |
| --- | --- |
| mode=`DISCOVER` | `references/supported-domain.md` + relevant page/design-contract references |
| level=`GLOBAL` | `references/global-design-contract.md` + applicable global rules |
| level=`PAGE` | page contract + applicable page rules |
| layer=`geometry` | `references/verification-stack.md` + GVH documentation |
| layer=`paint` | `references/paint-verification.md` |
| layer=`interaction` | `references/interaction-verification.md` |
| layer=`accessibility` | `references/accessibility-verification.md` |
| layer=`temporal` | `references/temporal-environmental-verification.md` |
| final verification | `references/ship-readiness.md` + proof/attestation documentation |

Load by **mode + hierarchy level + failure signal + verification layer**. Do not load the full rule library by default.

## Non-negotiable invariants

1. Top-down constraints.
2. Breadth before depth.
3. Fix at the lowest valid owner.
4. Escalate upward only when the root cause requires it.
5. Regress downward after a parent change.
6. Require evidence before reporting `FAIL`.
7. Required `UNKNOWN` blocks confirmation.
8. A fix must revalidate the same triggering rule.
9. A hard failure cannot be hidden by an aggregate quality score.
10. Geometry, paint, interaction, accessibility/semantics, and temporal/environmental verification remain distinct concerns.
11. Cached evidence is reusable only when its declared dependencies remain compatible.
12. `LOCKED` always refers to an identified snapshot and proof bundle.

## Proof requirements

Each verification rule declares a minimum proof level:

```text
observed | bounded | certified
```

When relevant it may also declare:

```text
execution | model | hybrid
```

Rules:

- `OBSERVED` evidence never satisfies a requirement for `BOUNDED` or `CERTIFIED` proof.
- Repeated sampling does not become a bound without a valid bounding method.
- A `CERTIFIED` result must be independently checkable by the applicable deterministic checker.
- Missing or invalid proof produces `UNKNOWN`, not a synthetic `PASS`.

## Finding ownership

Every finding has one primary owner:

```text
GLOBAL | FAMILY | PAGE | SECTION | COMPONENT | STATE | DETAIL
```

For correlated failures, run the Diagnosis Gate before patching:

```text
findings
→ dependency slice
→ smallest reproducible failure
→ root-cause candidate
→ valid owner
→ targeted fix
```

## Required fix loop

```text
finding
→ fix at lowest valid owner
→ rerun SAME triggering rule
→ targeted dependency-aware regression
→ close only after PASS
```

## Output discipline

Verification output must distinguish:

```text
PASS
FAIL
UNKNOWN
```

Do not replace `UNKNOWN` with inferred confidence.

When a structured violation/certificate format is applicable, follow the public rule schema and the formats documented in `docs/` and `references/`.

## Canonical public documentation

- `README.md` — public overview and entry point.
- `docs/01-pyramidal-stabilization.md` — stabilization method and ownership.
- `docs/02-agent-architecture-and-verification.md` — orchestration and verification model.
- `docs/03-geometric-visual-harness.md` — geometry engine.
- `docs/04-proof-evidence-attestation.md` — proof, provenance, and lock semantics.
- `docs/05-project-status-and-roadmap.md` — implemented vs planned capabilities.
