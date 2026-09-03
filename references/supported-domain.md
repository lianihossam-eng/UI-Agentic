# Supported Domain

A verification claim is meaningful only when the supported product surface is explicit.

UI-Agentic defines the Supported Domain as the set of factors the product actually claims to support and the verifier is expected to close.

Conceptually:

```text
Dₛ = Routes
   × Viewports
   × Containers
   × Content
   × States
   × Inputs
   × Locales
   × Environments
   × Time
```

A project contract can declare fields such as:

```yaml
supported_domain:
  routes: ["/", "/orders", "/settings"]
  viewport_widths: [320, 375, 768, 1024, 1440]
  viewport_height: 900
  containers: []
  content_extremes: []
  states: [default, modal-open]
  state_transition_models: []
  input_modalities: [mouse, keyboard]
  locales_directions: [en-LTR]
  browsers_platforms: [chromium]
  zoom_dpr: ["100% / DPR 1"]
  temporal_async_scenarios: [fonts-ready, geometry-stable]
  opaque_surface_adapters: []
  compliance_profiles: []
```

The exact schema used by the executable project may be narrower or more structured than this illustrative example.

## Scenario compilation

The Required Scenario Set is derived from the Supported Domain plus rule dependencies, contracts, and boundaries.

The compiler should not blindly execute the full Cartesian product. A rule is compiled over the factors that can affect it. Any declared independence or reduction must be explicit and defensible.

## Continuous and generated dimensions

Continuous ranges may require interval/boundary methods rather than discrete samples. Generated/property-based cases are useful for discovery but do not automatically certify an infinite domain.

## Opaque surfaces

If a required canvas/WebGL/cross-origin surface does not expose internal geometry or semantics through a verifiable adapter, internal obligations remain `UNKNOWN`.

## Confirmation meaning

`100% confirmed` means **100% of the required obligations derived from the declared Supported Domain are closed at their required proof level**.

It never means every imaginable UI/environment is covered.
