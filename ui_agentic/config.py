"""Project configuration and deterministic subject identity for UI-Agentic."""
from __future__ import annotations

import hashlib
import pathlib
from urllib.parse import urlparse

import yaml

CONFIG_NAME = ".ui-agentic.yaml"
STATE_DIR = ".ui-agentic"
_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    ".next",
    "dist",
    "build",
    STATE_DIR,
    "__pycache__",
}


class ConfigError(ValueError):
    """Raised when the project contract is missing or invalid."""


def default_config(base_url: str = "http://127.0.0.1:3000") -> dict:
    return {
        "version": 1,
        "app": {
            "base_url": base_url,
            "project_root": ".",
        },
        "supported_domain": {
            "routes": ["/"],
            "viewport_widths": [320, 375, 768, 1024, 1440],
            "viewport_height": 900,
            "states_by_route": {"/": ["default"]},
            "state_transition_models": [],
            "input_modalities": ["mouse", "keyboard"],
            "locales_directions": ["fr-LTR"],
            "browsers_platforms": ["chromium@playwright-managed"],
            "zoom_dpr": ["100%", "DPR 1"],
            "temporal_scenarios": ["fonts.ready", "geometry-stable"],
            "compliance_profiles": [],
        },
    }


def write_default_config(project_root: pathlib.Path, base_url: str, force: bool = False) -> pathlib.Path:
    path = project_root / CONFIG_NAME
    if path.exists() and not force:
        raise ConfigError(f"{CONFIG_NAME} already exists; use --force to replace it")
    project_root.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(default_config(base_url), sort_keys=False), encoding="utf-8")
    return path


def _validate_base_url(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError("app.base_url must be a non-empty http(s) URL")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigError("app.base_url must be an absolute http(s) URL")
    if parsed.query or parsed.fragment:
        raise ConfigError("app.base_url must not contain query or fragment")
    return value.rstrip("/")


def validate_config(config: dict) -> dict:
    if not isinstance(config, dict):
        raise ConfigError("configuration root must be a mapping")
    if config.get("version") != 1:
        raise ConfigError("unsupported configuration version")
    app = config.get("app")
    domain = config.get("supported_domain")
    if not isinstance(app, dict) or not isinstance(domain, dict):
        raise ConfigError("app and supported_domain mappings are required")
    app["base_url"] = _validate_base_url(app.get("base_url"))
    routes = domain.get("routes")
    widths = domain.get("viewport_widths")
    if not isinstance(routes, list) or not routes:
        raise ConfigError("supported_domain.routes must be a non-empty list")
    if any(not isinstance(route, str) or not route.startswith("/") for route in routes):
        raise ConfigError("every route must be an absolute application path beginning with /")
    if len(routes) != len(set(routes)):
        raise ConfigError("supported_domain.routes contains duplicates")
    if not isinstance(widths, list) or not widths or any(not isinstance(w, int) or w <= 0 for w in widths):
        raise ConfigError("supported_domain.viewport_widths must contain positive integers")
    if not isinstance(domain.get("viewport_height", 900), int) or domain.get("viewport_height", 900) <= 0:
        raise ConfigError("supported_domain.viewport_height must be a positive integer")
    states = domain.get("states_by_route", {})
    if not isinstance(states, dict):
        raise ConfigError("supported_domain.states_by_route must be a mapping")
    unknown_state_routes = set(states) - set(routes)
    if unknown_state_routes:
        raise ConfigError(f"states declared for unknown routes: {sorted(unknown_state_routes)}")
    return config


def load_config(project_root: pathlib.Path) -> dict:
    path = project_root / CONFIG_NAME
    if not path.exists():
        raise ConfigError(f"missing {CONFIG_NAME}; run `ui-agentic init` first")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return validate_config(data)


def resolve_source_root(project_root: pathlib.Path, config: dict) -> pathlib.Path:
    raw = config.get("app", {}).get("project_root", ".")
    if not isinstance(raw, str) or not raw:
        raise ConfigError("app.project_root must be a non-empty path")
    root = (project_root / raw).resolve()
    if not root.exists() or not root.is_dir():
        raise ConfigError(f"app.project_root does not exist or is not a directory: {root}")
    return root


def project_digest(root: pathlib.Path) -> str:
    """Hash the local application source tree deterministically.

    Volatile/generated verifier state, dependency/build directories and the
    UI-Agentic contract itself are excluded so changing the verification scope
    does not masquerade as a change to the application subject.
    """
    root = root.resolve()
    digest = hashlib.sha256()
    files: list[pathlib.Path] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if rel.as_posix() == CONFIG_NAME:
            continue
        if any(part in _EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.is_file() or path.is_symlink():
            files.append(path)
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix().encode()
        digest.update(len(rel).to_bytes(4, "big"))
        digest.update(rel)
        if path.is_symlink():
            payload = ("SYMLINK:" + str(path.readlink())).encode()
        else:
            payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()
