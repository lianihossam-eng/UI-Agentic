# Contributing to UI-Agentic

Thank you for considering a contribution to UI-Agentic.

UI-Agentic is an evidence-driven UI stabilization and verification project. Contributions are welcome, but changes to verification logic must preserve the project's fail-closed behavior, explicit ownership model, and proof discipline.

## Before you start

If you are new to the project, read:

1. `README.md`
2. `docs/00-project-guide.md`
3. `docs/GLOSSARY.md`
4. `docs/05-project-status-and-roadmap.md`
5. `docs/09-faq.md`

For architecture or verifier work, also read:

- `docs/01-pyramidal-stabilization.md`
- `docs/02-agent-architecture-and-verification.md`
- `docs/03-geometric-visual-harness.md` when geometry is involved
- `docs/04-proof-evidence-attestation.md`
- `docs/07-codebase-and-runtime-flow.md`
- `docs/08-extending-ui-agentic.md`

For external CLI work, read `docs/06-using-ui-agentic.md`.

For agent-oriented changes, also read `SKILL.md`.

## Core contribution principle

Every change should respect the hierarchy:

```text
GLOBAL → FAMILY → PAGE → SECTION → COMPONENT → STATE → DETAIL
```

A local patch must not silently redefine a higher-level contract.

When a defect belongs to a parent level, fix the parent and revalidate affected descendants rather than accumulating local overrides.

## Choose the right issue type

The repository provides structured issue templates under `.github/ISSUE_TEMPLATE/`.

Use:

- **Bug report** when UI-Agentic behaves incorrectly relative to its current contract;
- **Verification gap** when an important failure mode can escape the verifier or is not compiled as a required obligation;
- **Feature request** when proposing a new capability, integration, or product behavior.

For security vulnerabilities, do **not** open a public issue. See `SECURITY.md`.

## Opening a useful issue

A useful issue should include:

1. the affected area of the project;
2. the Supported Domain or verification scope involved;
3. expected behavior;
4. actual behavior;
5. reproduction steps when applicable;
6. evidence, logs, scenario IDs, rule IDs, or screenshots when useful;
7. the likely owner level if known;
8. whether the issue is a verifier defect, missing rule, documentation defect, or productization gap.

For verification gaps, describe the smallest counterexample that currently escapes the required claim.

## Pull request requirements

The repository includes `.github/PULL_REQUEST_TEMPLATE.md`. Complete the applicable sections rather than deleting trust-impact questions because they appear inconvenient.

For ordinary documentation or maintenance changes, keep the pull request focused and explain why the change is needed.

For verifier, rule, compiler, evidence, provenance, or attestation changes, include the following where applicable:

- affected requirement or failure mode;
- affected rule IDs;
- affected Supported Domain factors;
- hierarchy owner and verification layer;
- positive-path tests;
- negative-path or mutation/fault-injection coverage;
- proof that the triggering rule is revalidated;
- regression impact analysis;
- any new assumptions introduced;
- any change to evidence identity;
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

Use the proof model precisely:

```text
OBSERVED  — direct measurement of a rendered case
BOUNDED   — demonstrated bound over a declared region
CERTIFIED — independently checkable proof over the declared domain
```

Rules:

- repeated sampling does not become `BOUNDED` by repetition alone;
- a missing checker cannot produce `CERTIFIED`;
- missing or invalid evidence should produce `UNKNOWN`;
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

Avoid broad mutants that break many unrelated properties when a narrow targeted defect can test the intended checker more precisely.

## Trust-sensitive changes

Treat the following as more than ordinary refactors:

- reducing required scenario coverage;
- changing stable scenario/rule identities;
- weakening Measurement Readiness;
- converting unresolved cases from `UNKNOWN` to `PASS`;
- removing evidence-key inputs;
- weakening report/provenance bindings;
- weakening mutation requirements;
- changing visual-review equivalence;
- changing Trusted Verification Kernel membership;
- changing attestation inputs;
- expanding external `LOCKED` semantics;
- broadening compliance claims.

These changes can be valid, but they require explicit proof and documentation of why the stronger claim remains sound.

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

All public documentation must be written in clear, professional English.

Prefer:

- explicit terms over internal shorthand;
- one defined meaning per project term;
- stable architectural concepts over temporary CI numbers;
- exact capability boundaries over broad marketing claims;
- links to canonical documentation instead of duplicated explanations;
- `UNKNOWN` over unsupported certainty;
- short operational references over giant all-purpose prompts.

When introducing a new project-specific term, define it in `docs/GLOSSARY.md` if a public reader would otherwise have to infer its meaning.

When a public capability changes, update `docs/05-project-status-and-roadmap.md` in the same pull request.

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
3. proof and provenance integrity;
4. contract and ownership consistency;
5. regression safety;
6. clarity and maintainability;
7. performance only after the above remain intact.

## Merge discipline

Do not merge based on an earlier green commit when the pull-request head has moved.

The merge candidate should satisfy:

```text
exact reviewed PR head
        ↓
required CI complete
        ↓
all required jobs green
        ↓
no newer unreviewed commit
        ↓
merge
```

After a squash or merge creates a new `main` SHA, the resulting `main` workflow is the authoritative proof for that new commit.

## Public source-of-truth discipline

For a specific commit or release:

```text
executable code and CI behavior
        ↓
current contracts, rules, and Supported Domain
        ↓
core architecture documentation
        ↓
focused operational references
        ↓
historical archive material
```

If an implementation change makes a public claim inaccurate, update the relevant documentation in the same contribution.

## License

By contributing, you agree that your contribution will be licensed under the repository's MIT License.
