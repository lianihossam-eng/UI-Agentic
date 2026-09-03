---
name: ui-agentic
description: Orchestrateur pyramidal de stabilisation UI — 5 couches, preuves OBSERVED/BOUNDED/CERTIFIED, Evidence DAG.
---

# UI Agentic — SKILL.md (router)

Ce SKILL.md est le **seul point d'entrée**. Il route vers les références et règles, ne les duplique jamais.

## Workflow canonique (ROOT §4)
```
0 DECLARE Supported Domain
1 DISCOVER -> 2 CONTRACT -> 3 GLOBAL -> 4 FAMILIES -> 5 PAGE -> 6 SECTION/COMPONENT/STATE
7 MEASUREMENT READINESS -> 8 5-LAYER VERIFY -> 9 FINDINGS -> 10 DIAGNOSE -> 11 FIX lowest owner -> 12 REVALIDATE -> 13 REGRESSION -> 14 COVERAGE CLOSURE -> 15 VISUAL ACCEPTANCE -> 16 FINAL GATE -> 17 ATTESTATION -> 18 LOCK
```

## Modes (02 §2)
DISCOVER | DIRECTION | BUILD | AUDIT | VERIFY | REGRESSION | POLISH

Détection: argument `--mode` ou inférence par état du Coverage Ledger.

## Routing table
| Signal | Charge |
|---|---|
| mode=DISCOVER | references/supported-domain.md, references/page-contract.md |
| level=GLOBAL | references/global-design-contract.md + rules/global-*.md |
| level=PAGE | references/page-contract.md + rules/page-*.md |
| layer=geometry | references/verification-stack.md + GVH (03) |
| layer=paint | references/paint-verification.md |
| layer=interaction | references/interaction-verification.md |
| layer=accessibility | references/accessibility-verification.md |
| layer=temporal | references/temporal-environmental-verification.md |

## Invariants (ROOT §6)
- Top-down constraints. Breadth before depth. Lowest valid owner. Evidence before FAIL.
- UNKNOWN requis bloque CONFIRMED. Fix must revalidate same rule.
- Hard FAIL jamais masqué par score global.

## Preuve requise
Chaque règle déclare `required_proof: observed|bounded|certified` + `proof_source: execution|model|hybrid`. OBSERVED ne satisfait jamais BOUNDED/CERTIFIED.

## Sortie
Toute violation suit format `violation:` / `certificate:` (03 §16) et est validée par `scripts/validate_skill.py`.
