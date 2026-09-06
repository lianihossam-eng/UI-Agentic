# 08 — Extending UI-Agentic Safely

This document explains how to add new capabilities without weakening the verification claim.

UI-Agentic is not designed around a rule of “make the test suite green.” It is designed around a stricter rule:

> A new capability is acceptable only when its contract, applicability, evidence, failure behavior, and trust implications are explicit.

Use this guide when adding rules, states, transitions, adapters, proof checkers, verification layers, or final gates.

---

## 1. Extension principles

Every extension should preserve these invariants:

1. **Fail closed.** Missing required evidence becomes `UNKNOWN`, never an inferred `PASS`.
2. **Keep one owner.** Every rule or finding has one primary hierarchy owner.
3. **Keep concerns separated.** Geometry, paint, interaction, accessibility/semantics, and temporal/environmental verification remain distinct layers.
4. **Bind evidence to inputs.** New proof must not be reusable across incompatible subjects, contracts, scenarios, environments, or verifier versions.
5. **Test the verifier, not only the application.** Critical new failure modes should have negative-path or mutation coverage.
6. **Revalidate the same rule.** A fix is not closed merely because a broader suite later happens to be green.
7. **Do not broaden claims silently.** If a change expands the Supported Domain or compliance scope, document and compile that expansion explicitly.
8. **Update public status.** Architectural targets and implemented behavior must remain distinguishable.

---

## 2. Adding a verification rule

A new rule should begin with the requirement or failure mode it is meant to detect.

Do not start with an implementation trick such as “we can query this CSS property.” Start with the user-facing or contract-facing property that must hold.

A useful rule definition includes:

```yaml
id: page.example.no-hidden-submit
layer: interaction
owner: PAGE
detect: rendered
required_proof: observed
proof_source: execution
severity: high
scope: submit controls
applicability: pages with a required submit action
pass_condition: required submit control is visible and operable
assumptions: []
```

### Checklist

Before implementing the checker, answer:

- What exact requirement does the rule represent?
- Which hierarchy level owns the property?
- Which verification layer is primary?
- Does the rule require evidence from other layers?
- Which Supported Domain factors can affect the rule?
- What is the minimum proof level?
- What produces `PASS`?
- What produces `FAIL`?
- What produces `UNKNOWN`?
- What assumptions are required?
- Is the rule normative, product-contract-specific, or heuristic?

If these questions cannot be answered, the rule is not ready to become part of the confirmation contract.

---

## 3. Compile the rule over the correct domain

Adding a checker without adding required obligations can create false confidence.

The Scenario Compiler must know when and where the rule is required.

For example, if a rule depends on route, viewport, and UI state:

```text
rule dependencies
= route × viewport × state
```

then the compiler must generate obligations over the relevant classes or boundaries of those factors.

Do not rely on a checker being “available” during one replay. If the rule is required, its obligations must appear in the Required Scenario Set.

### Avoid accidental undercoverage

Bad:

```text
checker supports five viewports
compiler requires only one
```

The implementation looks capable, but four viewports are not part of the proof claim.

Good:

```text
dependencies declared
→ required scenarios compiled
→ every required record traceable
```

---

## 4. Implement the checker fail-closed

A checker should return one unambiguous result for the rule it owns.

Conceptually:

```python
{
  "constraint": "page.example.no-hidden-submit",
  "status": "PASS | FAIL | UNKNOWN",
  "proof_level": "observed",
  "evidence": {...}
}
```

### `PASS`

Use only when the positive condition was actually measured or proven.

### `FAIL`

Use only when valid evidence demonstrates a violation.

### `UNKNOWN`

Use when the checker cannot establish the property because of missing instrumentation, ambiguous targets, unsupported surfaces, failed readiness, insufficient proof strength, or another unresolved condition.

Never encode:

```text
no exception thrown → PASS
no matching element found → PASS
checker unavailable → PASS
empty measurement set → PASS
```

unless emptiness itself is explicitly the required positive condition.

---

## 5. Add Measurement Readiness requirements when needed

Some rules require a stronger readiness condition than others.

Examples:

- typography rules may depend on font readiness;
- layout rules may depend on image dimensions;
- async-state rules may depend on application hydration;
- animation rules may require a controlled clock rather than a static readiness window.

If a rule reads unstable state without proving readiness, its measurement may be invalid even if the checker code is correct.

Do not hide this with arbitrary sleeps.

---

## 6. Add traceability

Every required obligation should be traceable through:

```text
requirement / failure mode
        ↕
rule
        ↕
compiled scenario
        ↕
evidence record
        ↕
evidence key / certificate
```

A report that contains the right number of records but associates them with the wrong scenarios is not valid traceability.

Stable scenario IDs and rule IDs are therefore public proof infrastructure, not mere logging labels.

---

## 7. Add a mutation or negative-path test for critical rules

For a critical failure mode, create a defect that would have escaped the verifier before the new rule existed.

Expected pattern:

```text
baseline
  PASS

inject targeted defect
  ↓
new rule
  FAIL or UNKNOWN for the intended reason

revert defect
  ↓
baseline
  PASS
```

The mutation should be narrow enough that you can identify which verifier behavior killed it.

Avoid mutants that fail dozens of unrelated rules; they provide weaker evidence about the target rule.

---

## 8. Adding a new UI state

A state is not complete when it is merely listed in configuration.

For a new state:

1. define how the state is entered;
2. define readiness after entry;
3. define which rules are state-dependent;
4. compile those obligations;
5. define transitions into and out of the state;
6. define visual-review coverage if the state has visual significance;
7. define any cross-layer invariants;
8. add regression coverage.

Example:

```text
default
  -- open dialog -->
modal-open
  -- Escape -->
default
```

The state model should describe both state snapshots and meaningful transitions. State coverage alone does not prove transition correctness.

---

## 9. Adding a transition

A transition should define:

```text
source state
event / action
guard if applicable
target state
required effects
forbidden effects
round-trip expectations if applicable
```

A transition is not `PASS` because the target DOM exists in source code. The event must execute in the browser when the contract requires execution evidence.

When responsiveness can affect operability, the transition must be compiled over the relevant viewport classes rather than assumed to generalize from one width.

---

## 10. Adding a cross-layer invariant

Use a cross-layer invariant when the user-facing property genuinely cannot be established by one layer.

Examples:

```text
TARGET_OPERABLE
= geometry + hit testing + occlusion / interaction

FOCUS_USABLE
= keyboard focus + visibility + visual focus indication

MODAL_INTEGRITY
= geometry + interaction + focus + background operability
```

A cross-layer invariant should still have:

- one stable rule ID;
- one primary owner;
- one primary layer;
- an explicit list of required supporting layers;
- one atomic verdict.

Do not let one layer's `PASS` compensate for a failing required layer.

---

## 11. Adding a new proof level or certificate method

Do not create a new proof label merely because a method sounds stronger.

The existing levels are intentionally semantic:

```text
OBSERVED
BOUNDED
CERTIFIED
```

A new `BOUNDED` method must demonstrate an actual bound over its declared region.

A `CERTIFIED` method should produce a witness or certificate that a small deterministic checker can validate independently.

The strong-proof trust bundle should remain:

```text
contract
+ evidence / certificate
+ small deterministic checker
+ explicit assumptions
```

If the checker cannot validate the certificate, the result is `UNKNOWN`.

---

## 12. Adding an application adapter

An adapter exists to make an application observable without weakening the contract.

Examples include:

- HTTP navigation adapters;
- authenticated test-session adapters;
- deterministic data-fixture adapters;
- opaque-surface instrumentation adapters.

An adapter should expose facts, not manufacture positive verdicts.

For external applications, the adapter must not cause evidence from one application build to be reused for another. Subject identity and route/code identity must remain explicit.

For opaque surfaces such as canvas or WebGL, an adapter may expose internal geometry, but that geometry is trusted only to the degree that the instrumentation itself is in the declared trust boundary.

---

## 13. Adding a new browser or platform

Adding Firefox, WebKit, a mobile platform, or another runtime is not just a configuration change if the final claim will cover it.

You must consider:

- Supported Domain expansion;
- browser/runtime identity;
- environment-specific readiness;
- screenshot/rendering identity;
- rules whose applicability differs by platform;
- new failure modes;
- evidence-key changes;
- attestation inputs;
- CI matrix cost and determinism.

A multi-browser claim should be explicit about whether every required rule is closed on every browser or whether some rules have browser-specific applicability.

---

## 14. Extending the Geometric Visual Harness

Geometry extensions should preserve the Spatial Precision Ladder described in `docs/03-geometric-visual-harness.md`.

A more precise measurement should not silently pretend that unavailable precision was known before.

For example:

```text
layout box available
transformed polygon unavailable
```

If the decision requires the transformed polygon, the correct result is `UNKNOWN`, not a box-based guess presented as a precise answer.

When adding geometry:

- preserve coordinate-system identity;
- record clipping and transformation assumptions;
- separate broad-phase detection from precise decision logic;
- keep intentional overlap distinct from collision;
- keep stacking/paint order distinct from a fictional global z-axis.

---

## 15. Adding visual-review behavior

Visual review is a separate rubric layer.

If you change how visual equivalence is reused, you must preserve two identities:

1. **exact current-run screenshot identity** for artifact integrity;
2. **review-equivalence identity** only when a documented bounded equivalence rule justifies reuse.

Do not make an equivalence fingerprint so coarse that coherent visual changes can collide with approved output.

Changes to review equivalence should include adversarial tests, not only examples that are expected to remain stable.

---

## 16. Changing evidence identity

Changing evidence-key inputs is a trust change.

Before removing an input from evidence identity, prove that the input cannot affect the verified property or establish a valid assume→guarantee composition.

Before adding an input, understand the invalidation cost.

The goal is neither maximum caching nor maximum rerunning. The goal is **sound reuse**.

A useful question is:

> Could two runs differ in this input and legitimately produce different verdicts for the same rule?

If yes, the input usually belongs in the evidence identity or in a declared dependency that determines reuse.

---

## 17. Changing the Trusted Verification Kernel

A change to final decision logic, certificate checking, evidence reconstruction, provenance validation, scenario compilation, or another trusted component may change the Trusted Verification Kernel.

When this happens:

- update the kernel manifest if required;
- expect the kernel digest to change;
- do not attempt to preserve old attestation identity;
- add tests for the trust-boundary change;
- document any public claim that changed.

The verifier version changing is normal. Pretending an old verifier identity still represents new decision code is not.

---

## 18. Adding a final gate

A final gate should represent a condition that is required for the claim.

Do not add gates as decorative booleans.

A gate should be derived from evidence or independently recomputable state.

Good:

```text
critical_mutants_zero
= required mutation IDs exactly present
+ every mutant detected
+ no survivor
```

Weak:

```text
critical_mutants_zero = true
```

If the gate cannot be recomputed or validated independently, it remains part of the generator's assertion rather than strong evidence.

---

## 19. Updating documentation

When behavior changes, update the relevant public document in the same change.

Use the following map:

| Change | Update |
| --- | --- |
| Methodology / ownership | `docs/01-pyramidal-stabilization.md` |
| Scenario/compiler/verification architecture | `docs/02-agent-architecture-and-verification.md` |
| Geometry model | `docs/03-geometric-visual-harness.md` |
| Proof / provenance / attestation | `docs/04-proof-evidence-attestation.md` |
| Implemented capability boundary | `docs/05-project-status-and-roadmap.md` |
| CLI behavior | `docs/06-using-ui-agentic.md` |
| Source layout / runtime path | `docs/07-codebase-and-runtime-flow.md` |
| Extension requirements | this document |
| New public terminology | `docs/GLOSSARY.md` |

Do not update only the README when the change alters a normative or technical contract.

---

## 20. Pull request checklist for verifier changes

Before requesting review, confirm:

```text
[ ] requirement / failure mode is explicit
[ ] owner and verification layer are explicit
[ ] Supported Domain dependencies are explicit
[ ] required scenarios are compiled
[ ] checker is fail-closed
[ ] result.constraint matches the rule
[ ] proof level is correct
[ ] readiness is sufficient
[ ] traceability is preserved
[ ] evidence identity is correct
[ ] critical negative path / mutant is covered
[ ] same-rule revalidation exists
[ ] dependent regression runs
[ ] trusted-kernel implications are handled
[ ] public status and docs remain accurate
[ ] CI is green on the exact PR head
```

---

## 21. Changes that should trigger extra scrutiny

Treat these as trust-sensitive:

- reducing the Required Scenario Set;
- changing scenario IDs;
- converting `UNKNOWN` into `PASS`;
- adding default values to missing proof fields;
- weakening readiness;
- weakening visual equivalence;
- removing evidence-key inputs;
- changing report binding fields;
- changing attestation inputs;
- changing provenance checkers;
- changing mutation requirements;
- changing which files belong to the Trusted Verification Kernel;
- broadening compliance claims;
- broadening external `LOCKED` semantics.

These changes may be valid, but they should never be reviewed as ordinary refactors.

---

## 22. Recommended contributor workflow

```text
1. Identify requirement / failure mode
2. Read the relevant public specification
3. Locate the current implementation owner
4. Build the smallest failing reproducer
5. Add or adjust the rule / compiler / adapter
6. Add positive and negative-path tests
7. Run the same triggering rule
8. Run dependency-aware regression
9. Run the complete proof pipeline
10. Update public documentation
11. Merge only when CI is green on the exact reviewed SHA
```

This is the operational meaning of evidence-driven development inside UI-Agentic.
