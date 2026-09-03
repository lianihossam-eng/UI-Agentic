"""Content-address the browser measurement kernel used by Evidence DAG keys.

This digest is intentionally narrower than the full Trusted Verification Kernel:
it covers only scenario compilation, readiness, replay and rendered checkers that
can change the meaning of one Evidence DAG record. CI/finalizers/tests remain in
the broader trusted-kernel digest.
"""
from __future__ import annotations

import hashlib
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent

MEASUREMENT_KERNEL_FILES = (
    "core/measurement_kernel.py",
    "core/coverage.py",
    "core/scenario_compiler.py",
    "core/replay_engine.py",
    "gvh/extractor.py",
    "gvh/constraints.py",
    "gvh/paint.py",
    "gvh/interaction.py",
    "gvh/a11y.py",
    "gvh/temporal.py",
    "gvh/wcag.py",
    "gvh/verify.py",
)


def measurement_kernel_digest(base: pathlib.Path = BASE) -> str:
    """Full SHA-256 over canonical paths + exact measurement-kernel bytes."""
    h = hashlib.sha256()
    for relative in MEASUREMENT_KERNEL_FILES:
        path = base / relative
        if not path.is_file():
            raise FileNotFoundError(f"measurement-kernel file missing: {relative}")
        encoded = relative.encode("utf-8")
        content = path.read_bytes()
        h.update(len(encoded).to_bytes(4, "big"))
        h.update(encoded)
        h.update(len(content).to_bytes(8, "big"))
        h.update(content)
    return h.hexdigest()


def measurement_kernel_manifest(base: pathlib.Path = BASE) -> dict[str, str]:
    return {
        relative: hashlib.sha256((base / relative).read_bytes()).hexdigest()
        for relative in MEASUREMENT_KERNEL_FILES
    }
