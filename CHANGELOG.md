# Changelog

This file records public project milestones and user-visible changes.

UI-Agentic has not yet declared a stable `1.0` compatibility contract. Until tagged releases are established, the project follows an **Unreleased** development section and documents major public milestones rather than pretending every internal proof-pipeline iteration was a product release.

## Unreleased

### Documentation and public-readiness

- Rebuilt the public documentation around a complete A-to-Z project guide.
- Separated the three core specifications: pyramidal stabilization, agent architecture/verification, and the Geometric Visual Harness.
- Added a dedicated proof/evidence/attestation model.
- Added an explicit implementation-status and roadmap document so architectural targets are not confused with current executable capabilities.
- Added external CLI usage documentation, a repository/runtime-flow guide, an extension guide, glossary, FAQ, and public contributor guidance.
- Marked `archive/` as historical and non-normative.
- Standardized public documentation on clear English terminology.

### Productization

- Added the `ui-agentic` command-line entry point.
- Added project initialization, route discovery, external browser verification, report inspection, and a deliberately fail-closed external lock command.
- Decoupled the canonical replay engine from bundled `file://` fixtures so a running local HTTP application can be targeted through an adapter.
- Kept the external `LOCKED` claim disabled until the complete external subject / contract / verifier / evidence / visual / runtime attestation chain is authoritative.

### Verification and trust hardening

- Replaced synthetic or declarative trust paths with fail-closed evidence-derived gates.
- Made Measurement Readiness block rendered claims when readiness cannot be established.
- Executed required UI transitions in the browser rather than counting them as implicit passes.
- Added record-bound traceability between compiled obligations and evidence records.
- Added independent reconstruction of evidence identities and the Evidence DAG root.
- Added mutation/fault-injection coverage for critical verifier blind spots.
- Added runtime identity binding for relevant executables and rendering inputs.
- Added content-addressed Measurement Kernel and Trusted Verification Kernel identities.
- Added provenance tamper tests and pre-attestation checks.
- Made generic attestation generation provisional; authoritative `LOCKED` is reserved for the strict current-run finalization path.
- Added explicit visual acceptance with exact artifact identity and a bounded review-equivalence fingerprint that remains separate from exact screenshot hashes.

## 0.2 development line

The `0.2` development line introduced the first public external-project CLI surface while preserving the bundled reference proof pipeline as the stronger attested path.

Key user-visible capabilities include:

```text
ui-agentic init
ui-agentic discover
ui-agentic verify
ui-agentic report
ui-agentic lock
```

`ui-agentic lock` is intentionally fail-closed for external projects until the external attestation model reaches the same trust standard as the bundled reference pipeline.

## Historical prototype phase

Earlier repository history contains the experimental vertical-slice scripts now stored under `archive/`.

Those experiments were important in developing the current architecture, but they are not normative and should not be used to infer present verifier semantics.

For current behavior, use this order:

```text
exact code and CI for the evaluated commit
→ current contracts, rules, and Supported Domain
→ docs/
→ references/
→ archive/ only for historical context
```
