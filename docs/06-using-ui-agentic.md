# 06 — Using UI-Agentic on a Local Application

This guide explains how to use the stable public CLI against a running local web application.

It focuses on the current public product surface rather than the full target architecture.

For the conceptual model, read [Project Guide — UI-Agentic from A to Z](00-project-guide.md). For current implementation boundaries, read [05 — Implementation Status and Roadmap](05-project-status-and-roadmap.md).

---

## 1. Current CLI surface

The stable CLI exposes:

```text
ui-agentic init
ui-agentic discover
ui-agentic verify
ui-agentic report
ui-agentic lock
```

The first four commands provide a usable external-project verification workflow.

The external `lock` command is intentionally fail-closed in the stable version. It does not issue an authoritative external `LOCKED` attestation until the complete external subject/contract/verifier/evidence/runtime chain is generalized.

---

## 2. Requirements

You need:

- Python 3.10 or newer;
- Playwright;
- Chromium installed through Playwright;
- a local web application accessible through an HTTP or HTTPS URL.

A typical development setup is:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e /path/to/UI-Agentic
playwright install chromium
```

Then verify that the command is available:

```bash
ui-agentic --version
```

---

## 3. Start the application being verified

UI-Agentic targets the rendered application through HTTP.

For example, if your application runs at:

```text
http://127.0.0.1:3000
```

start that application first using its normal development or preview command.

UI-Agentic does not currently manage arbitrary application startup commands for you. The application must already be reachable when `discover` or `verify` runs.

---

## 4. Initialize the project contract

From the application project directory, run:

```bash
ui-agentic init --project . --base-url http://127.0.0.1:3000
```

This creates:

```text
.ui-agentic.yaml
```

The file is the external verification contract used by the stable CLI.

A generated contract currently resembles:

```yaml
version: 1
app:
  base_url: http://127.0.0.1:3000
  project_root: .

supported_domain:
  routes:
    - /

  viewport_widths:
    - 320
    - 375
    - 768
    - 1024
    - 1440

  viewport_height: 900

  states_by_route:
    /:
      - default

  state_transition_models: []

  input_modalities:
    - mouse
    - keyboard

  locales_directions:
    - fr-LTR

  browsers_platforms:
    - chromium@playwright-managed

  zoom_dpr:
    - 100%
    - DPR 1

  temporal_scenarios:
    - fonts.ready
    - geometry-stable

  compliance_profiles: []
```

The generated values are a starting contract, not a universal recommendation. Edit them so they describe the application you actually intend to verify.

---

## 5. Understand `app.project_root`

`app.project_root` identifies the local source tree used to derive the application's deterministic subject identity.

For a standard project where `.ui-agentic.yaml` lives at the application root:

```yaml
app:
  project_root: .
```

is appropriate.

The subject digest excludes common generated or volatile paths such as:

```text
.git/
.venv/
venv/
node_modules/
.next/
dist/
build/
.ui-agentic/
__pycache__/
```

and excludes `.ui-agentic.yaml` itself.

This separation is important:

```text
application source identity ≠ verification contract identity
```

Changing the verification scope should not pretend that the application source code itself changed.

---

## 6. Declare the Supported Domain

The most important configuration step is declaring what you actually support.

At minimum, the stable configuration validates:

- a non-empty route list;
- positive viewport widths;
- a positive viewport height;
- states attached only to declared routes;
- an absolute HTTP/HTTPS base URL.

Example:

```yaml
supported_domain:
  routes:
    - /
    - /orders
    - /settings

  viewport_widths:
    - 320
    - 375
    - 768
    - 1024
    - 1440

  viewport_height: 900

  states_by_route:
    /:
      - default
    /orders:
      - default
    /settings:
      - default
      - modal-open
```

Do not declare routes or states merely to make the contract look comprehensive. Every required declaration increases the proof obligation and should correspond to real supported behavior.

---

## 7. State support in the current replay engine

The current canonical replay engine supports the reference state model used by the project.

`default` requires no setup action.

`modal-open` expects an opener matching:

```text
[data-testid="open-modal"]
```

and a modal matching:

```text
[data-testid="modal"]
```

The modal state must become visibly open after activation.

This is a current implementation contract, not the final universal state-adapter architecture. Arbitrary external applications may require future adapters for richer state machines.

If a required state cannot be established, UI-Agentic should produce `UNKNOWN` rather than fabricating a pass.

---

## 8. Discover declared routes

Run:

```bash
ui-agentic discover --project .
```

`discover` visits each route declared in the Supported Domain and records basic rendered facts.

The output is written under:

```text
.ui-agentic/discovery.json
```

The discovery result includes information such as:

- route;
- resolved navigation target;
- HTTP status when available;
- document title;
- language/direction facts;
- a bounded list of links;
- control count;
- application project digest.

If declared routes cannot be reached, discovery returns a non-zero status rather than presenting the scan as complete.

---

## 9. Run verification

Run:

```bash
ui-agentic verify --project .
```

The command performs the core external workflow:

```text
load .ui-agentic.yaml
        ↓
validate contract
        ↓
resolve application source root
        ↓
compute project subject digest
        ↓
compile Supported Domain into scenarios
        ↓
resolve HTTP route targets
        ↓
launch Playwright / Chromium
        ↓
apply required state
        ↓
run Measurement Readiness
        ↓
extract rendered UI information
        ↓
run applicable verification checks
        ↓
record Coverage Ledger + evidence
        ↓
write external verification report
```

The current stable report is written to:

```text
.ui-agentic/verify.json
```

Current-run screenshots are written under:

```text
.ui-agentic/screenshots/
```

---

## 10. Interpreting verification output

The terminal summary reports values such as:

```text
PASS
FAIL
UNKNOWN
```

and coverage counts.

The important rule is:

```text
required obligation with valid positive evidence → PASS
required obligation with valid negative evidence → FAIL
required obligation without a valid verdict       → UNKNOWN
```

A closed run requires the required scenario set to be completely resolved under the current stable verifier.

`UNKNOWN` should be investigated, not converted into an ignore-by-default category.

Typical causes include:

- required UI state could not be established;
- Measurement Readiness failed;
- a checker could not produce one unambiguous result;
- the rendered application did not expose the expected contract;
- required instrumentation is unavailable.

---

## 11. Read the latest report

Run:

```bash
ui-agentic report --project .
```

The command prints the latest external verification summary, including the current subject digest, browser, coverage, failure/unknown counts, and evidence root.

Use it as a summary of the latest run, not as a replacement for inspecting the actual evidence when diagnosing a failure.

---

## 12. External project state directory

Generated verifier state is stored under:

```text
.ui-agentic/
```

Typical contents include:

```text
.ui-agentic/
├── discovery.json
├── verify.json
└── screenshots/
```

This directory is verifier-generated state and is deliberately excluded from the application subject digest.

That prevents the act of verification from changing the identity of the application being verified.

---

## 13. Attempting the lock gate

Run:

```bash
ui-agentic lock --project .
```

In the current stable external-project implementation, this command is deliberately conservative.

It first refuses obvious incomplete states such as:

- missing verification report;
- unclosed required scenario set.

Even after basic external verification closes, the stable public version still refuses to emit an authoritative external `LOCKED` verdict because the full external attestation chain is not yet generalized.

The missing trust chain is conceptually:

```text
SUBJECT
  exact external project identity

CONTRACT
  exact verification contract identity

VERIFIER
  exact installed UI-Agentic/checker identity

EVIDENCE DAG
  proof keys bound to subject + contract + verifier

VISUAL REVIEW
  required visual states and reviewer provenance

RUNTIME
  actual browser/executable/environment identity

FINAL GATE
  complete closure

ATTESTATION
  one content-addressed statement binding all inputs
```

Until that chain is authoritative, `NO LOCK` is the correct result.

---

## 14. Reference pipeline versus external CLI

The bundled UI-Agentic reference implementation has a stricter CI proof path than the current stable external CLI.

The reference pipeline includes additional gates such as:

```text
fault injection
traceability validation
proof-level validation
runtime identity
complete visual contract
provenance tamper tests
trusted-kernel checks
attestation finalization
LOCKED assertion
```

Do not infer that every one of those reference gates is already generalized automatically to any external application.

The current boundary is documented in [05 — Implementation Status and Roadmap](05-project-status-and-roadmap.md).

---

## 15. What a successful external `verify` proves today

A successful stable external verification run can establish that:

- the declared routes were mapped to the configured HTTP application;
- the current Supported Domain was compiled into required obligations supported by the current compiler;
- those obligations were executed through the canonical browser replay path;
- the current verifier closed its Coverage Ledger without required `FAIL` or `UNKNOWN` for that run;
- the report is associated with a deterministic application subject digest and browser evidence root.

It does **not** automatically prove:

- universal correctness outside the declared domain;
- complete accessibility conformance;
- all browsers/platforms;
- a mathematical bound over undeclared continuous ranges;
- a formal certificate for every rule;
- subjective visual quality;
- authoritative external `LOCKED` attestation.

---

## 16. Recommended first integration

For a new application, start deliberately narrow.

Example:

```text
one or two important routes
        ↓
default state
        ↓
320 / 375 / 768 / 1024 / 1440 widths
        ↓
mouse + keyboard
        ↓
Chromium / Playwright-managed
        ↓
fonts-ready + geometry-stable
```

Make that domain reliable first.

Then expand the contract only when the application and verifier adapters genuinely support the additional states, inputs, environments, or routes.

This follows the same project principle as the rest of UI-Agentic:

> Prefer a narrow, explicit, closed contract over a broad claim supported by incomplete evidence.

---

## 17. Troubleshooting

### `missing .ui-agentic.yaml`

Run:

```bash
ui-agentic init --project . --base-url http://127.0.0.1:3000
```

### `app.base_url must be an absolute http(s) URL`

Use an absolute URL such as:

```text
http://127.0.0.1:3000
```

not a relative path.

### Route discovery is incomplete

Confirm that:

- the application is already running;
- each configured route exists;
- the configured base URL is correct;
- the application does not require an authentication/session setup that the current adapter cannot yet establish.

### Required state becomes `UNKNOWN`

Confirm that the current state adapter supports it and that the page exposes the expected selectors/behavior.

For `modal-open`, inspect the current reference contract documented earlier in this guide.

### Verification reports `UNKNOWN` after navigation

Inspect the readiness information and the individual records in `.ui-agentic/verify.json`. The correct repair depends on why the measurement could not be trusted.

---

## 18. Next documents

After completing the first external run, read:

- [Supported Domain reference](../references/supported-domain.md)
- [Verification Stack](../references/verification-stack.md)
- [Proof, Evidence, and Attestation](04-proof-evidence-attestation.md)
- [Implementation Status and Roadmap](05-project-status-and-roadmap.md)
- [Verification Rules](../rules/README.md)
