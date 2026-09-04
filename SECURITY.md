# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately.

Do **not** open a public GitHub issue for a vulnerability that could expose users, credentials, CI infrastructure, artifact integrity, or verification trust boundaries.

Contact:

**lianihossam@gmail.com**

Include `UI-Agentic Security` in the subject line when possible.

## What to include

A useful report contains:

- a clear description of the vulnerability;
- affected component or file;
- reproduction steps or proof of concept;
- expected security impact;
- whether the issue requires specific runtime/CI conditions;
- suggested mitigation if you have one;
- any disclosure constraints or coordination request.

Please avoid including real secrets, unrelated personal data, or destructive payloads when a minimal reproduction is sufficient.

## Security-sensitive areas

Examples of security-relevant areas in UI-Agentic include:

- command execution and external-project adapters;
- CI workflow integrity;
- artifact and attestation provenance;
- evidence/report tampering;
- path traversal or unintended file access;
- unsafe parsing of external input;
- malicious HTML/application behavior during browser verification;
- dependency and package integrity;
- reviewer/identity spoofing;
- verifier or checker bypasses that could produce an unsupported `LOCKED` result.

A defect that only causes an incorrect verification result may still be security-relevant when it breaks the project's trust model.

## Response process

The maintainer will make a reasonable effort to:

1. acknowledge a credible report;
2. reproduce and classify the issue;
3. coordinate remediation and disclosure when necessary;
4. avoid publishing exploit details before an appropriate fix is available.

Response times depend on severity and maintainer availability. This project does not currently provide a commercial security SLA.

## Supported versions

Until formal releases are published, security fixes target the current public `main` branch unless otherwise stated.

When versioned releases are introduced, this section will be updated with an explicit support matrix.

## Disclosure

Please allow reasonable time for remediation before public disclosure of a confirmed vulnerability. Coordinated disclosure is preferred.

After remediation, the project may publish a security advisory or release note describing the issue and affected versions without exposing unnecessary sensitive details.
