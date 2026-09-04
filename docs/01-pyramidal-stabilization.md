# 01 — Pyramidal UI Stabilization System

This document defines the canonical stabilization method used by UI-Agentic.

Its scope is intentionally narrow: **work order, ownership, stabilization gates, change boundaries, escalation, and regression**. Verification architecture belongs in [02 — UI Agent Architecture & Verification](02-agent-architecture-and-verification.md). Objective geometric measurement belongs in [03 — Geometric Visual Harness](03-geometric-visual-harness.md).

---

## 1. Fundamental invariant

> A lower level must never solve a local problem by destabilizing a higher-level contract.

The hierarchy is:

```text
GLOBAL
  ↓
FAMILY
  ↓
PAGE
  ↓
SECTION
  ↓
COMPONENT
  ↓
STATE
  ↓
DETAIL
```

Constraints flow downward. Change requests escalate upward. Regression flows downward again.

This is the central anti-drift rule of the project.

---

## 2. Required work order

### Phase 0 — Discover

Map the product before changing its design system.

Discover at least:

- routes and surfaces;
- page families;
- shells and layout primitives;
- reusable components;
- critical states;
- overlays such as modals, drawers, popovers, and tooltips;
- responsive transformations;
- navigation and business constraints.

**Gate:** do not establish or rewrite the global design contract until the supported product surface is sufficiently understood.

### Phase 1 — Global

Define or extract the shared visual language:

- design intent;
- typography;
- semantic color system;
- spacing scale;
- global geometry;
- radii, borders, and elevation;
- motion principles;
- responsive philosophy;
- reusable primitives.

Represent the global system as a **Design IR** rather than a loose collection of local CSS values.

A global direction should be stress-tested on deliberately different surfaces before it becomes stable. A dense operational page, a transactional page, and a light content/marketing surface are useful stress cases when they exist in the product.

### Phase 2 — Family

A family owns structures shared by several pages, for example:

- application shell;
- navigation model;
- common page header;
- shared content container;
- density model;
- family-level responsive transformation;
- common loading/error architecture.

### Phase 3 — Page

A page owns:

- user objective;
- primary action;
- secondary actions;
- information hierarchy;
- macro layout;
- page-specific responsive behavior;
- critical page states;
- business constraints.

The macro layout must become stable before visual polish begins.

### Phase 4 — Section

For each section, stabilize:

```text
structure
→ dimensions
→ relationship to the page
→ responsive behavior
→ states
→ stability
```

### Phase 5 — Component

For each component, define and stabilize:

- anatomy;
- variants;
- geometry;
- token usage;
- internal responsive behavior;
- interaction states;
- accessibility behavior where applicable.

### Phase 6 — State and Transition

A happy path is not enough.

Relevant states can include:

```text
default
hover
focus
active
selected
disabled
loading
empty
error
success
short content
long content
low volume
high volume
missing media
permission variations
latency variations
```

For meaningful interactive flows, states must be connected by an explicit transition model:

```text
State --event [guard] / effect--> State
```

The model should identify:

- initial state;
- reachable states;
- required transitions;
- forbidden transitions;
- guards;
- effects;
- return paths and round trips;
- temporal invariants.

Complex products should compose smaller state machines rather than flatten every behavior into one global machine.

### Phase 7 — Detail

Only after structural stability:

- optical alignment;
- micro-spacing;
- icon weight;
- border/shadow refinement;
- letter spacing;
- motion timing.

Detail-level work must not silently change a stable page macro layout.

---

## 3. Breadth before depth

Stabilize horizontally across the product before polishing one surface deeply.

Bad sequence:

```text
Dashboard polished to completion
Orders unexplored
Settings unexplored
```

Preferred sequence:

```text
GLOBAL stable
↓
main page structures stable
↓
cross-page validation
↓
page-by-page refinement
```

This exposes weaknesses in global decisions while they are still inexpensive to correct.

---

## 4. Ownership model

Every important property should have one primary owner.

| Level | Typical ownership |
| --- | --- |
| GLOBAL | spacing scale, semantic palette, radii, typography scale, global responsive principles |
| FAMILY | sidebar, application shell, family container, common page header |
| PAGE | macro grid, zone ordering, page-specific density |
| SECTION | toolbar, local grid, relationships among blocks |
| COMPONENT | internal padding, anatomy, variants, control sizing |
| STATE | loading, empty, error, disabled, selected, modal-open behavior |
| DETAIL | optical offsets, micro-spacing, fine visual nuance |

A descendant should not arbitrarily redefine a property owned by an ancestor.

---

## 5. Change Boundary System

Before applying a local correction:

1. identify the real owner of the property;
2. check whether an existing primitive or variant already solves the problem;
3. fix at the lowest level capable of solving the root cause without violating parent constraints;
4. escalate upward only when necessary.

### Upward escalation

```text
DETAIL
→ STATE / COMPONENT
→ SECTION
→ PAGE
→ FAMILY
→ GLOBAL
```

### Downward regression

When a parent changes:

```text
parent change
↓
dependency graph
↓
affected descendants become stale/unverified
↓
rerun impacted obligations
```

The purpose is not to rerun everything blindly. The purpose is to invalidate exactly the evidence that depends on the changed contract.

---

## 6. Stabilization states

```text
UNEXPLORED
→ DRAFT
→ STRUCTURED
→ STABLE
→ VERIFIED
→ LOCKED
```

Definitions:

- **UNEXPLORED** — the surface has not been sufficiently mapped.
- **DRAFT** — direction exists but is intentionally provisional.
- **STRUCTURED** — architecture and relationships are defined but still freely changeable.
- **STABLE** — reliable enough to allow work to proceed to descendants.
- **VERIFIED** — applicable verification obligations have passed with required evidence.
- **LOCKED** — an identified snapshot is covered by a valid verification attestation; changes require impact analysis and revalidation.

A descendant cannot be considered `VERIFIED` if a required parent contract is not sufficiently stable.

---

## 7. Minimum gates

### Global Gate

- coherent Design IR;
- coherent tokens and primitives;
- typography, spacing, colors, radii, and elevation agree with the contract;
- responsive philosophy is explicit;
- stress-test surfaces are validated;
- no applicable global hard constraint is violated.

### Family Gate

- shell and navigation are coherent;
- shared containers and headers are stable;
- family responsive transformations are explicit and stable;
- common states are accounted for.

### Page Gate

- objective and hierarchy are clear;
- macro layout is stable;
- family contract is respected;
- responsive transformations are stable;
- critical states and content boundaries are represented;
- no unjustified local override masks a parent problem.

### Section / Component / State Gate

- anatomy and relationships are explicit;
- token and parent contracts are respected;
- required variants and states are covered;
- significant flows include required transition checks;
- relevant content extremes are handled;
- keyboard/touch behavior is verified when part of the Supported Domain.

### Detail Gate

- changes are polish-only;
- parent constraints remain unchanged;
- no new arbitrary design value is introduced without ownership.

---

## 8. Hard and soft constraints

### Hard constraints

Hard failures cannot be compensated by aesthetics.

Examples:

- unintended overflow;
- unauthorized collisions;
- required content hidden;
- inaccessible required controls;
- broken navigation;
- insufficient required hit target;
- violation of locked tokens or contracts;
- invalid overlay behavior.

### Soft constraints

Soft criteria can be optimized only after hard constraints are closed.

Examples:

- balance;
- rhythm;
- whitespace;
- perceived density;
- symmetry;
- visual interest;
- refinement quality.

---

## 9. Responsive ownership

Responsive behavior follows the same hierarchy.

- **GLOBAL** — responsive philosophy, type/spacing scaling, global containers.
- **FAMILY** — shell and navigation transformations.
- **PAGE** — zone order and macro layout.
- **SECTION** — grid-to-stack transitions, wrapping toolbars, local structure.
- **COMPONENT** — internal adaptation of a component.

A component must not invent a local responsive policy that contradicts its parent.

---

## 10. Anti-patterns

Without an explicit architectural reason, avoid:

- arbitrary local spacing values;
- raw colors that bypass semantic tokens;
- one-off radii;
- undeclared button sizes;
- improvised component-specific breakpoints;
- duplicate near-identical components;
- CSS overrides whose only purpose is to hide a symptom;
- fixing several correlated symptoms independently when they share one parent cause.

---

## 11. Canonical stabilization output

```text
DISCOVER
→ GLOBAL STABLE
→ FAMILIES STABLE
→ PAGES STRUCTURALLY STABLE
→ SECTIONS / COMPONENTS STABLE
→ STATES / TRANSITIONS VERIFIED
→ DETAILS POLISHED
→ REGRESSION
→ LOCK
```

---

## 12. Definition of done for the method

The stabilization method is being followed correctly when:

- every important design property has an owner;
- every hierarchy level has an explicit gate;
- local work cannot silently override parent contracts;
- correlated failures are diagnosed before patching;
- fixes are applied at the lowest valid owner;
- parent changes invalidate dependent evidence;
- `LOCKED` is treated as controlled change over an attested snapshot, not as permanent immutability.
