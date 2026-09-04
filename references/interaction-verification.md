# Interaction Verification

Interaction verification checks whether users can actually operate the rendered interface through the input modalities declared by the Supported Domain.

## Verify when applicable

- hit testing;
- pointer/click behavior;
- touch behavior;
- keyboard actions;
- focus movement;
- scrolling;
- drag/gesture behavior;
- open/close interactions;
- state transitions;
- required and forbidden transition paths;
- round-trip behavior such as open → close → focus return.

## Transition model

Meaningful flows should be represented explicitly:

```text
State --event [guard] / effect--> State
```

Verifying isolated states is not sufficient when correctness depends on how the user reaches or leaves those states.

## Evidence

Use real browser actions and observed state/effect evidence whenever the rule is rendered/interaction-based.

A transition must not receive `PASS` merely because the destination state exists in the DOM.

## Cross-layer invariants

Interaction evidence can be combined with geometry, accessibility, and paint evidence for rules such as:

- `TARGET_OPERABLE`;
- `FOCUS_USABLE`;
- `MODAL_INTEGRITY`;
- `ASYNC_STABILITY`.
