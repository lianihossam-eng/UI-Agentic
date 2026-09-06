## Summary

<!-- What changed and why? Keep the change focused. -->

## Change type

- [ ] Documentation only
- [ ] Bug fix
- [ ] Verification rule / checker
- [ ] Scenario compiler / Supported Domain
- [ ] Browser replay / Measurement Readiness
- [ ] Evidence / provenance / attestation
- [ ] CLI / application adapter
- [ ] Refactor with no intended claim change
- [ ] Other

## Verification claim impact

<!-- State explicitly whether this changes what UI-Agentic claims to verify. -->

- [ ] No public verification claim changes
- [ ] Required Scenario Set changes
- [ ] PASS / FAIL / UNKNOWN semantics change
- [ ] Proof-level requirements change
- [ ] Evidence identity / reuse changes
- [ ] Trusted Verification Kernel changes
- [ ] Visual Acceptance semantics change
- [ ] External `LOCKED` semantics change
- [ ] Compliance scope changes

## Requirement / failure mode

<!-- For verifier changes: what exact requirement or failure mode is this change responsible for? -->

## Owner and layer

<!-- Example: COMPONENT / interaction, PAGE / geometry, STATE / temporal. -->

## Evidence and testing

- [ ] Positive-path test or evidence added/updated
- [ ] Negative-path / mutation coverage added when critical
- [ ] Same triggering rule revalidated
- [ ] Dependency-aware regression considered
- [ ] Required `UNKNOWN` remains fail-closed
- [ ] No hard failure is hidden by an aggregate score

Evidence / commands / run links:

```text
paste relevant evidence here
```

## Trust-boundary review

<!-- Complete when verifier/proof logic changes. -->

- [ ] Scenario compilation remains complete for the declared dependencies
- [ ] Result constraint matches the compiled rule
- [ ] Measurement Readiness is sufficient for rendered evidence
- [ ] Evidence keys bind every relevant input
- [ ] Report/provenance bindings remain independently checkable
- [ ] Mutation requirements are not weakened
- [ ] Trusted-kernel membership/digest implications are handled
- [ ] Attestation inputs remain snapshot-bound

## Documentation

- [ ] Public documentation is unchanged and remains accurate
- [ ] Relevant docs/status/glossary files were updated in this PR

## Final merge gate

- [ ] CI is green on the exact PR head being reviewed
- [ ] No newer unreviewed commit was pushed after the verified SHA
