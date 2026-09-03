# UI-Agentic

> Un seul workflow pour concevoir, stabiliser, vérifier et verrouiller une UI avec preuves — de la pyramide au pixel.

**Statut public actuel:** architecture **STABLE** • moteur de validation exécutable **AUDITÉ / fail-closed** • ancienne attestation `db1a1f55a1bdda6e` **STALE** après suppression de chemins `PASS` synthétiques • nouvelle confirmation requise avant tout statut `LOCKED`.

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
├── run_goal_verify.py
└── .goal_attestation.json
```

## Supported Domain exécutable actuel

Le fichier `supported-domain.yaml` sépare désormais explicitement :

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

## Quickstart

```bash
python -m pip install -e .
playwright install chromium
python run_goal_verify.py
```

Le runner est volontairement **fail-closed** : tant que les gates externes ne sont pas fournis, il termine sans nouvelle attestation `LOCKED`.

## Corrections issues de l’audit public indépendant

La publication GitHub a permis de détecter plusieurs défauts que les rapports précédents ne permettaient pas de voir :

1. plusieurs règles recevaient un `PASS` synthétique dans le runner final ;
2. `measurement_readiness()` contenait un `or True` qui neutralisait le gate ;
3. les transitions étaient comptées comme `PASS` sans événement réellement exécuté ;
4. l’attestation pouvait retourner `LOCKED` sans valider le Final Confirmation Gate ;
5. le README revendiquait un périmètre WCAG/ACT plus large que l’implémentation publique.

Ces chemins ont été supprimés ou reclassés. Désormais :

```text
preuve réelle → PASS
preuve négative → FAIL
preuve absente / checker absent → UNKNOWN
Final Gate incomplet → NO LOCK
```

L’ancienne attestation `db1a1f55a1bdda6e` est donc conservée uniquement comme historique et marquée `STALE`.

## Gates encore nécessaires avant une nouvelle attestation

Le runner exige désormais explicitement les gates suivants :

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

## Preuves honnêtes

- sampling seul = `OBSERVED`, jamais `BOUNDED` ;
- `UNKNOWN` bloque la confirmation ;
- aucune attestation `LOCKED` si le Final Gate n’est pas `PASS` ;
- Evidence DAG inclut code, contrat, règle, scénario, navigateur, checker et environnement ;
- toute modification d’une entrée de preuve invalide l’attestation correspondante.

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
→ Visual Acceptance indépendant
→ nouvelle attestation
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

Le dépôt GitHub est désormais la source auditable de l’implémentation publique. Notion reste la source de conception et de coordination de l’équipe.
