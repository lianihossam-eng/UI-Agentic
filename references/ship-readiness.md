# Ship Readiness

A UI snapshot is ready for final confirmation only when all applicable hard gates are closed.

## Minimum closure conditions

- required Supported Domain obligations compiled;
- required coverage closed;
- hard `FAIL = 0`;
- required `UNKNOWN = 0`;
- required proof levels satisfied;
- measurement readiness satisfied;
- requirement/failure-mode traceability complete;
- critical mutation/fault adequacy closed;
- no unrevalidated fixes;
- no open required regressions;
- parent contracts valid;
- required state/transition obligations complete;
- required cross-layer invariants complete;
- declared compliance obligations closed when applicable;
- visual acceptance `ACCEPTED`;
- attestation provenance valid for the exact snapshot.

## Release rule

No aggregate score can override a missing required proof, hard failure, unresolved required unknown, or invalid provenance.

`LOCKED` is emitted only for an identified snapshot and evidence bundle. Any material change requires impact analysis and revalidation.
