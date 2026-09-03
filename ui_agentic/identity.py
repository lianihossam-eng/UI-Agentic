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


def _package_roots(package_name: str) -> list[pathlib.Path]:
    module = __import__(package_name)
    roots: list[pathlib.Path] = []
    module_paths = getattr(module, "__path__", None)
    if module_paths is not None:
        roots.extend(pathlib.Path(item).resolve() for item in module_paths)
    else:
        module_file = getattr(module, "__file__", None)
        if module_file:
            roots.append(pathlib.Path(module_file).resolve().parent)
    unique = sorted({root for root in roots if root.exists() and root.is_dir()})
    if not unique:
        raise RuntimeError(f"cannot resolve verifier package roots for {package_name}")
    return unique


def verifier_source_manifest() -> dict[str, str]:
    """Hash installed verifier Python sources independent of checkout location."""
    manifest: dict[str, str] = {}
    for package_name in ("ui_agentic", "core", "gvh"):
        package_roots = _package_roots(package_name)
        for root_index, root in enumerate(package_roots):
            prefix = package_name if len(package_roots) == 1 else f"{package_name}@{root_index}"
            for path in sorted(root.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                rel = f"{prefix}/{path.relative_to(root).as_posix()}"
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                existing = manifest.get(rel)
                if existing is not None and existing != digest:
                    raise RuntimeError(f"verifier source manifest collision for {rel}")
                manifest[rel] = digest
    if not manifest:
        raise RuntimeError("verifier source manifest is empty")
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
