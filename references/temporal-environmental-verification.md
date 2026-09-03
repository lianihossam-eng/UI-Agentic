# Temporal and Environmental Verification

Temporal/environmental verification checks whether UI behavior remains valid across the declared runtime conditions and time-dependent states.

## Typical concerns

- font loading;
- image/asset resolution;
- hydration;
- async loading and state transitions;
- virtualization;
- animation and transition timing;
- layout stability;
- locale/direction;
- zoom and DPR;
- browser/platform identity;
- dynamic viewport behavior;
- mobile keyboard effects when declared;
- deterministic fixture/network state.

## Measurement readiness

Rendered measurement should begin only after the declared readiness conditions are satisfied.

A readiness gate can require:

```text
expected application state reached
+ required fonts resolved
+ required assets in expected state
+ hydration/async state settled
+ geometry stable for declared observation window
+ controlled time/randomness/environment where relevant
```

A fixed sleep is not proof of readiness.

If readiness cannot be established, affected rendered obligations become `UNKNOWN`.

## Temporal rules

When motion itself is part of the contract, control time and verify the required `G(t)` states/events rather than forcing only the final frame.

The temporal layer may participate in composite invariants such as `ASYNC_STABILITY` and `MODAL_INTEGRITY`.
