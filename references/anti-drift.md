# Anti-Drift Rules

UI-Agentic prevents local fixes from silently fragmenting a stable design system.

## Core rules

1. Every important property has a primary owner.
2. Descendants must respect parent contracts.
3. Fix at the lowest valid owner capable of solving the root cause.
4. Escalate upward only when the current owner cannot solve the problem safely.
5. After a parent change, invalidate and reverify affected descendants.
6. Do not introduce arbitrary local values when a declared token or primitive should own the decision.
7. Do not duplicate near-identical components to avoid fixing a shared cause.
8. Do not use CSS overrides solely to hide symptoms.
9. A fix is incomplete until the same triggering rule is revalidated.
10. Cached evidence is reusable only when its declared dependencies still match.

## Typical drift signals

- repeated one-off spacing values;
- page-specific colors that bypass semantic tokens;
- local breakpoints contradicting family/global responsive rules;
- duplicate component variants with no contract-level distinction;
- local z-index escalation to compensate for a layer-model problem;
- several symptom-level patches caused by one parent constraint.

## Required response

```text
drift signal
→ identify owner
→ diagnose dependency/root cause
→ fix at lowest valid owner
→ rerun triggering rule
→ dependency-aware regression
```
