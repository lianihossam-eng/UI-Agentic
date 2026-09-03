# Contributing

Merci pour votre intérêt pour UI-Agentic.

## Workflow

Toute contribution suit `GLOBAL → FAMILY → PAGE → ... → LOCK` (01). Pas de patch local hors ownership.

1. Ouvrir une issue avec Supported Domain impacté
2. Proposer le fix au lowest valid owner
3. Revalider la même règle + regression ciblée (Evidence DAG)
4. Fournir preuve OBSERVED/BOUNDED honnête (jamais BOUNDED par sampling)
5. Mettre à jour le Coverage Ledger — 100% requis pour CONFIRMED

Voir `SKILL.md` pour le routing et `references/`.

## Anti-triche

- UNKNOWN préféré à faux PASS
- BOUNDED seulement avec enclosure + checker
- Mutants critiques doivent être tués (0 survived)

## Dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install playwright && playwright install chromium
python run_goal_verify.py
```
