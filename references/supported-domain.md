# Supported Domain (02 §5)

Avant toute confirmation, déclarer explicitement ce qui est supporté.

```yaml
supported_domain:
  routes: ["/", "/orders", "/settings"]
  viewport_ranges: { width: [320, 1920], height: [600, 1080] }
  containers: ["main: [720, 1152]"]
  states: [default, hover, focus, loading, empty, error]
  state_transition_models: ["order-flow: State --event [guard] / effect --> State"]
  content_extremes: ["label: 1..120 chars", "items: 0..200"]
  input_modalities: [mouse, keyboard, touch]
  locales_directions: ["fr-LTR", "ar-RTL"]
  browsers_platforms: ["chromium@latest"]
  zoom_dpr: ["100%, 150%, 200%", "DPR 1,2"]
  temporal_async_scenarios: ["hydration", "fonts.ready", "lazy-image"]
  opaque_surface_adapters: []
  compliance_profiles: [{standard: WCAG, version: "2.2", level: AA, scope: full-pages}]
```

Réduction implicite interdite. Toute indépendance doit être justifiée.
