# 04 — Proof, Evidence, and Attestation Model

This document explains how UI-Agentic turns browser observations into auditable verification claims.

The project intentionally separates **what was observed**, **what was proven over a region**, **what was independently certified**, and **what was accepted subjectively**.

---

## 1. Why the proof model exists

UI verification becomes unreliable when different kinds of evidence are collapsed into one score.

Examples of unsafe reasoning:

- “We tested many widths, therefore the entire responsive interval is proven.”
- “The screenshot looks fine, therefore keyboard focus is correct.”
- “The solver says the property is valid, therefore the certificate is trustworthy.”
- “The previous run passed, therefore this commit is still locked.”

UI-Agentic prevents these shortcuts by binding each claim to an explicit proof level and evidence identity.

---

## 2. Proof levels

### OBSERVED

A property was measured directly for one rendered scenario.

Typical examples:

- no overflow at 768 px;
- modal focus remained inside during one declared transition;
- contrast ratio passed for a rendered element under one environment;
- the target received the expected hit test.

Observed evidence is local to its scenario.

### BOUNDED

A valid bound was established over a declared region of the domain.

Examples can include:

- an interval method proves a geometric residual remains below tolerance over a width interval;
- adaptive subdivision closes every region of a declared continuous range;
- a mathematical enclosure establishes a property under explicit assumptions.

A large sample set does not become `BOUNDED` merely because it is large.

### CERTIFIED

A property is demonstrated over the declared domain by an applicable certification method and validated by an independent checker.

A certified claim should include:

```text
property
+ domain
+ certificate/witness
+ assumptions
+ independent deterministic checker
```

If the checker cannot validate the witness, the claim is not certified.

---

## 3. Evidence types

Proof level and evidence type are different concepts.

### Static evidence

Derived from source/configuration without rendering:

- configuration;
- AST/source inspection;
- design tokens;
- rule definitions;
- dependency manifests.

### Rendered evidence

Derived from a real browser/runtime:

- DOM geometry;
- computed styles;
- hit testing;
- keyboard behavior;
- screenshots;
- environment identity;
- timing/stability observations.

### Rubric evidence

Derived from explicit qualitative review:

- design hierarchy;
- visual coherence;
- density/whitespace;
- brand fidelity;
- comparison against reference imagery.

Rubric evidence can be rigorous and auditable without pretending to be a formal certificate.

---

## 4. Fail-closed semantics

The verifier follows a strict three-state model:

```text
PASS
FAIL
UNKNOWN
```

### PASS

The required evidence exists and satisfies the rule.

### FAIL

The required evidence exists and demonstrates a violation.

### UNKNOWN

The verifier cannot legitimately decide.

Examples:

- measurement readiness was not established;
- the required DOM surface is opaque;
- a checker is missing;
- evidence binding does not match the current subject;
- a certificate is malformed;
- a required transition could not be executed.

A required `UNKNOWN` blocks final confirmation.

This is deliberate. Missing evidence must never be converted into a synthetic `PASS`.

---

## 5. Evidence identity

Evidence is reusable only when the inputs that determine its meaning remain compatible.

A conceptual evidence key is:

```text
hash(
  subject/code identity
+ contract
+ rule
+ scenario
+ browser/build
+ platform/runtime
+ fonts/assets
+ locale/DPR
+ verifier/checker identity
)
```

The exact implementation can evolve, but the principle is stable: **a proof is inseparable from the inputs that produced it**.

---

## 6. Evidence DAG

UI-Agentic stores evidence as a dependency graph rather than a flat list of test results.

This enables two important behaviors.

### Targeted invalidation

When a parent contract or code input changes, evidence that depends on that input becomes stale.

### Safe reuse

Evidence whose complete declared dependency set remains compatible may be reused.

This is the basis of dependency-aware regression.

The goal is neither “rerun everything” nor “cache everything.” The goal is **reuse only when provenance still matches**.

---

## 7. Measurement kernel vs evidence generator

UI-Agentic distinguishes between:

- the code that **generates measurements/evidence**; and
- the smaller trusted code that **checks critical proof conditions**.

Agents, search procedures, fuzzers, optimizers, numerical solvers, and even large orchestration scripts should not automatically belong to the trusted core.

The smaller the final trust boundary, the easier it is to audit.

---

## 8. Trusted Verification Kernel

The intended final trust bundle is:

```text
contract
+ evidence/certificate
+ small deterministic checker
+ explicit assumptions
```

The checker should validate the result rather than reproduce every step taken by the generator.

For example, a solver may search a large state space, but the final checker should validate the witness using a smaller deterministic procedure whenever possible.

---

## 9. Rule adequacy and mutation testing

Passing every current rule does not prove that the rules are complete.

UI-Agentic therefore treats the mapping between failure modes and rules as a separate verification problem.

Required traceability is conceptually:

```text
requirement / failure mode
↔ rule
↔ required scenario
↔ evidence
```

Mutation/fault-injection tests challenge the verifier by creating known bad conditions.

A critical mutant is successful only when the verifier reports `FAIL` or `UNKNOWN` for the intended reason and the reverted baseline returns to `PASS`.

A surviving critical mutant blocks strong confirmation because it demonstrates a blind spot in the verifier.

---

## 10. Assumptions

Every strong proof claim depends on assumptions.

Examples:

- a browser/runtime version;
- font identity;
- deterministic fixture data;
- a declared locale;
- a model-to-browser conformance assumption;
- a stable network fixture;
- a rendering environment.

Assumptions must be explicit and attributable to the evidence they support.

An unstated assumption is a provenance defect.

---

## 11. Runtime identity

Rendered evidence can depend on runtime details even when source code does not change.

A runtime identity can include:

- operating system;
- Python runtime;
- Playwright version;
- Chromium binary identity;
- browser version;
- font file identities;
- relevant system/runtime configuration.

The attestation should bind the runtime identity whenever it materially affects the evidence.

---

## 12. Visual evidence

Screenshots have two separate roles.

### Exact run evidence

Exact file hashes identify the actual bytes rendered in one run.

### Review identity

When the project allows bounded raster-equivalence for subjective review reuse, a separate deterministic review fingerprint may represent the approved visual equivalence class.

These identities must not be confused.

Exact snapshot identity is evidence of what the runtime produced. A review fingerprint is only an explicitly defined mechanism for deciding whether a previous human/agent visual review can be reused.

---

## 13. Visual acceptance provenance

A valid visual approval should identify:

```text
visual contract
reviewed snapshot or equivalence-class identity
reviewer identity
reviewer type
review timestamp
reviewed states
reviewed image count
rubric
verdict
```

A reviewer must never be attributed implicitly.

If an agent performed the review, the record should identify an agent. If a human performed the review, the record should identify the human only when that review actually occurred.

---

## 14. Report provenance

A report should not be considered current merely because its internal hash is valid.

A report must also be bound to the current verification context, for example:

```text
subject / commit identity
scenario digest
rules digest
checker digest
environment manifest digest
evidence root
run identity
```

A stale but internally well-formed report is still stale.

---

## 15. Final Confirmation Gate

The Final Gate is a conjunction of required closure conditions.

It must never be implemented as a collection of manually trusted booleans detached from evidence.

Conceptually:

```text
proof artifact
↓
deterministic checker
↓
gate verdict
↓
Final Confirmation Gate
↓
Verification Attestation
```

Missing or invalid proof should produce a blocking result, not a default `true`.

---

## 16. Verification Attestation

The attestation is the final content-bound record of the verified snapshot.

A mature attestation can include:

```yaml
subject:
  identity: ...

contract: ...
scenario_digest: ...
rules_digest: ...
checker_digest: ...
measurement_kernel_digest: ...
trusted_kernel_digest: ...
environment_manifest_digest: ...
runtime_identity_root: ...
evidence_root: ...
reports_root: ...
visual_evidence_root: ...
source_run_id: ...
final_gate: ...
verdict: LOCKED
```

The exact schema is versioned and can evolve.

---

## 17. Why `LOCKED` is snapshot-bound

A lock is valid for an identified subject under an identified contract and evidence bundle.

If any material input changes:

```text
change
↓
impact analysis
↓
affected evidence becomes stale
↓
required revalidation
↓
new final gate
↓
new attestation
```

Therefore `LOCKED` means **controlled change**, never permanent immutability.

---

## 18. Authority of CI attestations

For the bundled reference implementation, the authoritative lock is generated by the complete CI proof pipeline rather than by a committed static attestation file.

This avoids a recursive problem where an attestation claims to contain the digest of the commit that itself contains the attestation.

The CI artifact can bind the exact tested commit/run without modifying the commit afterward.

---

## 19. External-project attestation

The external-project CLI is being generalized in stages.

The required identities are conceptually separate:

```text
SUBJECT
  bytes/identity of the external application

CONTRACT
  Supported Domain and verification contract

VERIFIER
  content-addressed identity of the UI-Agentic verifier
```

A future authoritative external lock must additionally bind:

- Evidence DAG entries to the external contract;
- visual review to the external subject/contract/verifier;
- distributed verifier provenance;
- runtime identity;
- complete final-gate closure.

Until those responsibilities are authoritative, the external CLI must remain fail-closed instead of emitting a misleading `LOCKED` result.

---

## 20. Proof-model invariants

1. Sampling is `OBSERVED` unless a stronger method is demonstrated.
2. Required `UNKNOWN` blocks confirmation.
3. A certificate without an independent applicable checker is not `CERTIFIED`.
4. Missing evidence never becomes `PASS` by default.
5. Report hashes do not replace current-run provenance.
6. Visual review is subjective evidence and stays separate from formal proof.
7. Evidence reuse requires compatible declared dependencies.
8. A fix is not closed until the triggering rule is revalidated.
9. Critical surviving mutants block strong verification claims.
10. `LOCKED` always identifies a snapshot, contract, verifier, environment, and evidence bundle.
