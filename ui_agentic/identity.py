"""Content-addressed identities for external-project verification."""
from __future__ import annotations

import hashlib
import json
import pathlib

from core.measurement_kernel import measurement_kernel_digest
from ui_agentic import __version__


def canonical_json_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def contract_digest(config: dict) -> str:
    """Hash only the normative external verification contract."""
    return canonical_json_digest(
        {
            "schema": "ui-agentic-external-contract-v1",
            "supported_domain": config["supported_domain"],
        }
    )


def verifier_source_manifest() -> dict[str, str]:
    """Hash installed verifier Python sources independent of checkout location."""
    roots: list[tuple[str, pathlib.Path]] = []
    for package_name in ("ui_agentic", "core", "gvh"):
        module = __import__(package_name)
        module_file = pathlib.Path(module.__file__).resolve()
        roots.append((package_name, module_file.parent))

    manifest: dict[str, str] = {}
    for package_name, root in roots:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = f"{package_name}/{path.relative_to(root).as_posix()}"
            manifest[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest


def verifier_digest() -> str:
    return canonical_json_digest(
        {
            "schema": "ui-agentic-verifier-v1",
            "version": __version__,
            "measurement_kernel_digest": measurement_kernel_digest(),
            "sources": verifier_source_manifest(),
        }
    )


def verifier_identity() -> dict:
    manifest = verifier_source_manifest()
    return {
        "version": __version__,
        "measurement_kernel_digest": measurement_kernel_digest(),
        "verifier_digest": canonical_json_digest(
            {
                "schema": "ui-agentic-verifier-v1",
                "version": __version__,
                "measurement_kernel_digest": measurement_kernel_digest(),
                "sources": manifest,
            }
        ),
        "source_files": len(manifest),
    }
