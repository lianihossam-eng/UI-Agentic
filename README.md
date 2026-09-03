# UI-Agentic

> Un seul workflow pour concevoir, stabiliser, vérifier et verrouiller une UI avec preuves — de la pyramide au pixel.

**Statut public actuel:** architecture **STABLE** • moteur de validation exécutable **AUDITÉ / fail-closed** • vertical slice public `90/90` sur le Supported Domain déclaré • un commit n’est `LOCKED` que lorsque son workflow GitHub `proof-gates` est entièrement vert et que l’artefact CI du même run contient l’attestation finale autoportante.

## Le principe

```text
GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL
```

Invariant : *un niveau inférieur ne peut jamais déstabiliser un supérieur*. Contraintes descendent, escalades montent, régressions redescendent.

## Workflow A→Z

```text
0 DECLARE Supported Domain
→ 1 DISCOVER
→ 2 CONTRACT
→ 3 GLOBAL
→ 4 FAMILIES
→ 5 PAGE
→ 6 SECTION / COMPONENT / STATE / TRANSITION
→ 7 MEASUREMENT READINESS
→ 8 5-LAYER VERIFY
→ 9 FINDINGS
→ 10 DIAGNOSE
→ 11 FIX lowest valid owner
→ 12 REVALIDATE same rule
→ 13 DEPENDENCY-AWARE REGRESSION
→ 14 COVERAGE CLOSURE
→ 15 VISUAL ACCEPTANCE
→ 16 FINAL CONFIRMATION GATE
→ 17 ATTESTATION
→ 18 LOCK
```

`100% CONFIRMED` signifie uniquement : **100% du Required Scenario Set dérivé du Supported Domain déclaré**, avec chaque niveau de preuve requis satisfait, `FAIL=0`, `UNKNOWN=0`, tous les gates externes fermés et Visual Acceptance `ACCEPTED`.

Cela ne signifie jamais « toutes les UIs imaginables » ni « tous les environnements possibles ».

## 5 couches

| Couche | Vérifie actuellement | État public |
|---|---|---|
| **geometry** | boxes, gaps, containment, spacing scale | exécutable |
| **paint** | contraste rendu sur fond effectif | exécutable, partiel |
| **interaction** | hit-test, taille cible, modal integrity | exécutable |
| **accessibility** | ordre clavier + focus visible/non obscurci | exécutable, partiel |
| **temporal** | fonts/assets + stabilité géométrique | exécutable, partiel |

Cross-layer actuels : `TARGET_OPERABLE`, `FOCUS_USABLE`, `MODAL_INTEGRITY`.

> WCAG 2.2 AA complet, ACT/axe-core, touch, contenu extrême, multi-browser et domaine responsive continu restent des **extensions cibles**, pas des garanties actuelles.

## Structure

```text
UI-Agentic/
├── SKILL.md
├── supported-domain.yaml
├── references/
├── rules/
├── gvh/
├── core/
├── assets/templates/
├── evaluations/
├── archive/
├── scripts/
├── reports/visual_approval.json
└── run_goal_verify.py
```

`.goal_attestation.json` est **généré au runtime par CI et ignoré par Git**. Il n’est pas versionné, car une attestation qui prétend lier le SHA du commit qui la contient créerait une référence récursive impossible à rendre exacte. L’autorité est donc l’artefact GitHub Actions produit par le run du commit attesté.

## Supported Domain exécutable actuel

Le fichier `supported-domain.yaml` sépare explicitement :

- `supported_domain` : facteurs réellement visés par le runner public ;
- `target_domain_extensions` : fonctionnalités futures qui **ne comptent pas** dans la confirmation actuelle.

Le domaine exécutable actuel comprend :

- routes `/orders`, `/settings`, `/analytics` ;
- largeurs discrètes `320, 375, 768, 1024, 1440` ;
- Chromium géré par Playwright, version exacte enregistrée au run ;
- souris + clavier ;
- `fr-LTR` ;
- DPR 1 / zoom 100% ;
- transitions modales réelles sur `/settings` et `/analytics`.

Le domaine continu `[320,1440]`, touch, WCAG 2.2 AA complet, contenu extrême et scénarios async avancés sont actuellement hors confirmation.

## Visual Acceptance v3

Le gate visuel est **exact-snapshot**, pas portable.

La matrice actuelle comprend :

```text
3 routes × 5 viewports en état default       = 15 images
2 routes modales × 5 viewports en modal-open = 10 images
                                                ---------
                                                 25 images
```

Le digest du snapshot est calculé à partir des digests des 25 fichiers. Une approbation n’est valable que pour **un seul digest exact** et doit contenir :

- reviewer explicite (`reviewer_type=agent`, `reviewer=agent:<id>` dans la CI actuelle) ;
- timestamp de revue ;
- portée `default + modal-open` ;
- nombre exact d’images ;
- digest exact du bundle revu ;
- verdict `ACCEPTED` ou `REJECTED`.

Un autre rendu pixel, même fonctionnellement équivalent, nécessite un nouvel enregistrement d’approbation. Il n’existe plus de whitelist `accepted_snapshots` ni d’attribution implicite à un humain.

## Quickstart

```bash
python -m pip install -e .
playwright install chromium
python run_goal_verify.py
```

Le runner est volontairement **fail-closed** : une preuve absente, un report invalide, un binding incohérent ou un Visual Acceptance non accepté bloque le `LOCKED`.

## Corrections issues de l’audit public indépendant

La publication GitHub a permis de détecter plusieurs défauts que les rapports initiaux ne permettaient pas de voir :

1. plusieurs règles recevaient un `PASS` synthétique dans le runner final ;
2. `measurement_readiness()` contenait un `or True` qui neutralisait le gate ;
3. les transitions étaient comptées comme `PASS` sans événement réellement exécuté ;
4. l’attestation pouvait retourner `LOCKED` sans valider le Final Confirmation Gate ;
5. le README revendiquait un périmètre WCAG/ACT plus large que l’implémentation publique ;
6. des reports pouvaient être rebindés au run courant sans être réellement régénérés ;
7. une ancienne preuve visuelle pouvait être transférée entre plusieurs snapshots ;
8. une identité humaine pouvait être déclarée sans mécanisme de preuve ;
9. le Final Gate visuel était encore câblé sur `15` screenshots alors que les états modaux devaient aussi être revus ;
10. une attestation runtime ancienne était versionnée dans le dépôt et pouvait être confondue avec l’attestation du HEAD courant.

Ces chemins ont été supprimés ou rendus fail-closed. Désormais :

```text
preuve réelle → PASS
preuve négative → FAIL
preuve absente / checker absent → UNKNOWN
Final Gate incomplet → NO LOCK
Visual snapshot différent → nouvelle revue
attestation autoritative → artefact CI du commit exact
```

L’ancienne attestation `db1a1f55a1bdda6e` et les anciennes attestations locales sont uniquement historiques et ne constituent pas une preuve du HEAD courant.

## Final Confirmation Gate

Le runner exige explicitement :

```text
requirement_traceability
required_proof_levels
certificate_validation
measurement_readiness
critical_mutants_zero
unstated_assumptions_zero
regression_closed
parent_contracts_valid
state_transitions_complete
cross_layer_invariants_complete
compliance_obligations_complete
visual_acceptance
```

Un gate absent ou non démontré bloque la confirmation.

Le workflow CI ajoute en plus :

```text
unit tests
→ fault injection 7 classes
→ semantic current-run evidence
→ complete visual contract
→ GOAL verification
→ strict visual gate
→ provenance tamper tests
→ self-contained attestation
→ strict current-run provenance gate
→ LOCKED assertion
→ immutable Actions artifact
```

## Autorité de l’attestation

Pour un commit donné, la preuve autoritative est le bundle GitHub Actions du **même SHA**. L’attestation finale lie notamment :

```text
commit_sha
source_run_id
scenario_digest
rules_digest
checker_digest
environment_manifest_digest
evidence_root
reports_root
visual_evidence_root
final_gate
```

Le strict provenance gate recalcule les hashes de reports, le runtime Python/Playwright/Chromium, les bytes des screenshots, le snapshot visuel et le digest de l’attestation avant de permettre `LOCKED`.

## Preuves honnêtes

- sampling seul = `OBSERVED`, jamais `BOUNDED` ;
- `UNKNOWN` bloque la confirmation ;
- aucune attestation `LOCKED` si le Final Gate n’est pas `PASS` ;
- Evidence DAG inclut code, contrat, règle, scénario, navigateur, checker et environnement ;
- toute modification d’une entrée de preuve invalide l’attestation correspondante ;
- une revue visuelle ne se transfère jamais vers un digest pixel différent.

## Publication / contribution

- Licence : **MIT**
- Contributions : voir `CONTRIBUTING.md`
- Sécurité : voir `SECURITY.md`
- Code of Conduct : voir `CODE_OF_CONDUCT.md`

### Release candidate open source

Une release candidate ne doit être créée qu’après :

```text
clean replay
→ fault injection / mutation adequacy
→ deterministic reproduction
→ gates externes fermés
→ Visual Acceptance exact-snapshot
→ attestation CI autoportante
→ strict provenance PASS
→ LOCKED
```

## Documentation canonique

La documentation de conception reste organisée autour de :

```text
ROOT — workflow canonique
01 — Pyramidal UI Stabilization System
02 — UI Agent Architecture & Verification
03 — Geometric Visual Harness (GVH)
README — façade humaine / publication
```

Le dépôt GitHub est la source auditable de l’implémentation publique. Notion reste la source de conception et de coordination de l’équipe.
