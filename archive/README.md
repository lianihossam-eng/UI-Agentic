# Archive

This directory contains historical experiments, intermediate runners, and earlier vertical-slice implementations kept for traceability.

## Important

Files under `archive/` are **not normative** and are not part of the current public API, verification architecture, or trusted execution path.

Do not use archived scripts as the source of truth for:

- the canonical workflow;
- Supported Domain semantics;
- proof levels;
- current verification rules;
- evidence or provenance requirements;
- attestation generation;
- external-project CLI behavior;
- release readiness.

The current public sources of truth are:

```text
README.md
docs/
SKILL.md
references/
rules/
supported-domain.yaml
ui_agentic/
core/
gvh/
scripts/
.github/workflows/
```

Historical files may intentionally contain outdated assumptions, temporary APIs, superseded proof logic, or incomplete experiments. They are preserved to make the project's evolution auditable, not to provide supported examples.

When documentation and an archived implementation disagree, the current documentation and executable verifier take precedence.
