"""Content-address the complete Trusted Verification Kernel.

Every authoritative proof artifact must bind this digest. The manifest includes
this file itself, all measurement/checker code, all final gates/finalizers, and
the CI recipe + dependency lock that execute them.
"""
from __future__ import annotations

import hashlib
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent

TRUSTED_KERNEL_FILES = (
    "core/trust_kernel.py",
    "core/coverage.py",
    "core/scenario_compiler.py",
    "core/attestation.py",
    "gvh/extractor.py",
    "gvh/constraints.py",
    "gvh/paint.py",
    "gvh/interaction.py",
    "gvh/a11y.py",
    "gvh/temporal.py",
    "gvh/wcag.py",
    "gvh/verify.py",
    "run_goal_verify.py",
    "scripts/capture_current_run_evidence.py",
    "scripts/build_traceability_report.py",
    "scripts/enforce_visual_contract.py",
    "scripts/strict_visual_gate.py",
    "scripts/pre_attestation_gate.py",
    "scripts/finalize_current_run_attestation.py",
    "scripts/strict_provenance_gate.py",
    "scripts/strict_kernel_attestation_gate.py",
    "scripts/fault_injection.py",
    ".github/workflows/proof-gates.yml",
    "requirements-ci.txt",
)


def trusted_kernel_digest(base: pathlib.Path = BASE) -> str:
    """Return full SHA-256 over path names + exact bytes in canonical order."""
    h = hashlib.sha256()
    for relative in TRUSTED_KERNEL_FILES:
        path = base / relative
        if not path.is_file():
            raise FileNotFoundError(f"trusted-kernel file missing: {relative}")
        encoded = relative.encode("utf-8")
        content = path.read_bytes()
        h.update(len(encoded).to_bytes(4, "big"))
        h.update(encoded)
        h.update(len(content).to_bytes(8, "big"))
        h.update(content)
    return h.hexdigest()


def trusted_kernel_manifest(base: pathlib.Path = BASE) -> dict[str, str]:
    """Return per-file SHA-256s for diagnostics and independent replay."""
    return {
        relative: hashlib.sha256((base / relative).read_bytes()).hexdigest()
        for relative in TRUSTED_KERNEL_FILES
    }
