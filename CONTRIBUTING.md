# Contributing to UI-Agentic

Thank you for considering a contribution to UI-Agentic.

UI-Agentic is an evidence-driven verification project. Contributions are welcome, but changes to verification logic must preserve the project's fail-closed behavior and explicit proof model.

## Before you start

Please read:

- `README.md`
- `docs/01-pyramidal-stabilization.md`
- `docs/02-agent-architecture-and-verification.md`
- `docs/04-proof-evidence-attestation.md`
- `docs/05-project-status-and-roadmap.md`

For agent-oriented changes, also read `SKILL.md`.

## Core contribution principle

Every change should respect the hierarchy:

```text
GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL
```

A local patch must not silently redefine a higher-level contract.

When a defect belongs to a parent level, fix the parent and revalidate affected descendants rather than accumulating local overrides.

## Opening an issue

A useful issue should include:

1. the affected area of the project;
2. the Supported Domain or verification scope involved;
3. expected behavior;
4. actual behavior;
5. reproduction steps when applicable;
6. evidence, logs, or screenshots when useful;
7. the likely owner level if known;
8. whether the issue is a verifier defect, missing rule, documentation defect, or productization gap.

For security vulnerabilities, do **not** open a public issue. See `SECURITY.md`.

## Pull request requirements

For ordinary documentation or maintenance changes, keep the pull request focused and explain why the change is needed.

For verifier, rule, compiler, evidence, provenance, or attestation changes, include the following where applicable:

- affected requirement/failure mode;
- affected rule IDs;
- affected Supported Domain factors;
- positive-path tests;
- negative-path or mutation/fault-injection coverage;
- proof that the triggering rule is revalidated;
- regression impact analysis;
- any new assumptions introduced;
- any change to the trusted verification boundary;
- documentation updates when public behavior changes.

## Required fix loop

A defect is not considered closed merely because code was changed.

```text
finding
→ diagnose root cause
→ fix at lowest valid owner
→ rerun the SAME triggering rule
→ targeted dependency-aware regression
→ close only after evidence passes
```

## Proof discipline

Use the proof model honestly:

```text
OBSERVED  — direct measurement of a rendered case
BOUNDED   — demonstrated bound over a declared region
CERTIFIED — independently checkable proof over the declared domain
```

Rules:

- repeated sampling does not become `BOUNDED` by repetition alone;
- a missing checker cannot produce `CERTIFIED`;
- missing/invalid evidence should produce `UNKNOWN`;
- a required `UNKNOWN` blocks confirmation;
- aggregate scores must never mask hard failures.

## Mutation and fault-injection expectations

Changes to a critical verifier path should demonstrate that the verifier can detect the failure mode it claims to cover.

A useful mutation test establishes:

```text
baseline PASS
→ injected defect
→ verifier FAIL or UNKNOWN for the intended reason
→ revert defect
→ baseline PASS again
```

A surviving critical mutant is evidence of a verifier blind spot.

## Development setup

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project and browser dependency:

```bash
python -m pip install -e .
playwright install chromium
```

Run the Python unit tests:

```bash
python -m unittest discover -s tests -v
```

Run the bundled reference verifier:

```bash
python run_goal_verify.py
```

The GitHub Actions workflow performs additional mutation, provenance, visual, runtime, and attestation gates. A local `run_goal_verify.py` success is not equivalent to the complete CI `LOCKED` path.

## Documentation style

Public documentation must be written in clear English.

Prefer:

- explicit terms over internal shorthand;
- stable architectural concepts over temporary CI numbers;
- exact capability boundaries over broad marketing claims;
- links to canonical documentation instead of duplicated explanations;
- `UNKNOWN` over unsupported certainty.

## Commit and pull request scope

Keep commits and pull requests cohesive when practical.

Examples:

- documentation cleanup should not silently alter verifier semantics;
- productization work should not weaken proof gates to make a demo pass;
- verifier refactors should preserve or strengthen the trusted boundary;
- historical experiments should not be treated as normative implementation.

## Code review priorities

Reviewers should prioritize:

1. correctness of the verification claim;
2. fail-closed behavior;
3. proof/provenance integrity;
4. contract and ownership consistency;
5. regression safety;
6. clarity and maintainability;
7. performance only after the above remain intact.

## License

By contributing, you agree that your contribution will be licensed under the repository's MIT License.
