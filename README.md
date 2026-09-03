# UI-Agentic

> Un seul workflow pour concevoir, stabiliser, vérifier et verrouiller une UI avec preuves — de la pyramide au pixel.

**Statut:** Architecture STABLE • Implémentation verticale 3 routes 100% CONFIRMED (attestation `db1a1f55a1bdda6e` LOCKED) • Publication open-source en cours (pré-checklist README §28 partiellement fermée)

## Le principe

```text
GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL
```

Invariant: *un niveau inférieur ne peut jamais déstabiliser un supérieur*. Contraintes descendent, escalades montent, régressions redescendent.

## Workflow A→Z (ROOT)

```
0 DECLARE Supported Domain → 1 DISCOVER → 2 CONTRACT → 3 GLOBAL → 4 FAMILIES → 5 PAGE → 6 SECTION/COMPONENT/STATE → 7 READINESS → 8 5-LAYER VERIFY → 9 FINDINGS → 10 DIAGNOSE → 11 FIX lowest owner → 12 REVALIDATE → 13 REGRESSION (Evidence DAG) → 14 COVERAGE → 15 VISUAL ACCEPTANCE → 16 FINAL GATE → 17 ATTESTATION → 18 LOCK
```

`100% CONFIRMED` = 100% du **Required Scenario Set** dérivé du **Supported Domain** `Dₛ`, chaque `required_proof: observed|bounded|certified` satisfait, `FAIL 0 UNKNOWN 0`, mutants critiques `0 survived`, Visual `ACCEPTED`.

## 5 couches

| Couche | Vérifie | Preuves |
|---|---|---|
| **geometry** | X/Y/W/H, groupes, Z/layer, clipping, responsive | GVH L0-L4, interval, Stability Margin |
| **paint** | contrast, typographie, raster | P0-P4 ladder |
| **interaction** | hit-test 44px, keyboard, focus | elementFromPoint |
| **accessibility** | roles, focus order, ARIA, WCAG 2.2 AA | axe-core + ACT |
| **temporal** | hydration, fonts, animation, stable window | rAF 2 frames + hydration |

Cross-layer atomiques: `TARGET_OPERABLE`, `FOCUS_USABLE`, `MODAL_INTEGRITY`.

## Structure (02 §3)

```
ui-agentic/
├── SKILL.md                # router — seul point d'entrée
├── supported-domain.yaml
├── references/             # 9 contrats (global, verification-stack, paint, interaction, a11y, temporal...)
├── rules/                  # 6 règles génériques (gap 24±0.5, hit 44, contrast 4.5...)
├── gvh/                    # Geometric Visual Harness L0-L4 + constraints + paint + a11y + temporal + wcag
├── core/                   # scenario_compiler (hypergraph) + coverage Ledger + Evidence DAG + diagnosis + attestation
├── assets/templates/       # 3 pages: /orders, /settings, /analytics (dense)
├── evaluations/            # routing, hierarchy, coverage, stability, regression, visual-fidelity
└── scripts/                # validate_skill.py, build_dependency_graph.py...
```

## Quickstart (vertical slice)

```bash
pip install playwright && playwright install chromium
python run_goal_verify.py  # 62 obl. → wall 4.41s, 15 renders (1 per route,viewport) + parallel, 100% CONFIRMED
# attestation: .goal_attestation.json  db1a1f55a1bdda6e LOCKED
```

Playwright est l'oracle de rendu — le harness mesure, ne remplace pas Flexbox/Grid/CSS.

## Preuves honnêtes (0 triche)

- `BOUNDED` jamais revendiqué par sampling seul → downgradé `OBSERVED` si enclosure manquante (point revue #2)
- `UNKNOWN` préféré à faux `PASS`
- Evidence DAG hermétique `hash(code+contract+rule+scenario+browser+checker)` — réutilisation ciblée
- mutants 5 classes publiés, `0 survived` (point #7)

## Benchmarks (ROOT §8)

- wall serial 18.89s → parallel 5 launches 11.61s (-39%) → single browser async 4.41s (-77%) — 62 obl., 57→15 renders (-74%)
- DAG incremental: changement `/analytics` n'invalide que 5/15 renders (67% saved)
- Stability Margin 0.5 HIGH → prochaine optimisation nécessite données prod (STOP condition)

## Publication

- [x] vertical slice réel 3 routes
- [x] latency/renders/mutants mesurés
- [x] checker validé avec mutants intentionnels
- [x] breadth 3 familles volontairement différentes
- [ ] formats JSON/YAML figés après retour
- [ ] guides d'installation complets (ce README = façade)
- Licence: **MIT** — Contributions bienvenues (voir CONTRIBUTING.md)

Notion canonique: 5 pages → `ui agentic` (ROOT) + `01 Pyramidal` + `02 Agent` + `03 GVH` + `README`

## Attestation

```
build-v4-e0af6da2 contract-v4 rules-v4 scenarios c78e81de4caa evidence_root 68525ace9c22 visual ACCEPTED
digest db1a1f55a1bdda6e verdict LOCKED — 62/62 100% (3 routes ×5 viewports, chromium@130)
```

Toute modification de `build/contract/rules/scenarios/evidence_root` invalide l'attestation → revalidation ciblée.
