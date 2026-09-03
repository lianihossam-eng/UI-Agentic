"""Command-line interface for using UI-Agentic against another local project."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from core.replay_engine import replay
from core.scenario_compiler import compile as compile_scenarios
from ui_agentic import __version__
from ui_agentic.app_adapter import HttpAppAdapter
from ui_agentic.config import (
    ConfigError,
    STATE_DIR,
    load_config,
    project_digest,
    resolve_source_root,
    write_default_config,
)


def _project(value: str | None) -> pathlib.Path:
    return pathlib.Path(value or ".").resolve()


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    root = _project(args.project)
    path = write_default_config(root, args.base_url, force=args.force)
    print(f"created {path}")
    print("next: edit supported_domain, start the app, then run `ui-agentic discover`")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    root = _project(args.project)
    config = load_config(root)
    app = config["app"]
    routes = config["supported_domain"]["routes"]
    discovered = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        for route in routes:
            target = urljoin(app["base_url"].rstrip("/") + "/", route.lstrip("/"))
            try:
                response = page.goto(target, wait_until="domcontentloaded")
                facts = page.evaluate(
                    """() => ({
                      title: document.title,
                      lang: document.documentElement.lang || '',
                      dir: getComputedStyle(document.documentElement).direction || 'ltr',
                      links: Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.getAttribute('href')).filter(Boolean).slice(0, 100),
                      controls: document.querySelectorAll('button,a[href],input,select,textarea').length
                    })"""
                )
                discovered.append({
                    "route": route,
                    "target": target,
                    "status": response.status if response else None,
                    **facts,
                })
            except Exception as exc:
                discovered.append({"route": route, "target": target, "error": str(exc)})
        browser.close()
    source_root = resolve_source_root(root, config)
    report = {
        "product_version": __version__,
        "project_digest": project_digest(source_root),
        "base_url": app["base_url"],
        "routes": discovered,
    }
    out = root / STATE_DIR / "discovery.json"
    _write_json(out, report)
    failures = [item for item in discovered if item.get("error") or (item.get("status") or 200) >= 400]
    print(f"discovered {len(discovered)} declared routes -> {out}")
    if failures:
        print(f"discovery incomplete: {len(failures)} route(s) unreachable", file=sys.stderr)
        return 2
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    root = _project(args.project)
    config = load_config(root)
    domain = config["supported_domain"]
    source_root = resolve_source_root(root, config)
    source_digest = project_digest(source_root)
    adapter = HttpAppAdapter(
        config["app"]["base_url"],
        source_digest,
        tuple(domain["routes"]),
    )
    scenarios = compile_scenarios(domain)
    state = root / STATE_DIR
    result = replay(
        domain=domain,
        scenarios=scenarios,
        route_targets=adapter.navigation_targets(),
        route_code_digests=adapter.code_digests(),
        capture_screenshots=True,
        screenshot_dir=state / "screenshots",
    )
    report = {
        "product_version": __version__,
        "subject": {
            "project_root": str(source_root),
            "project_digest": source_digest,
            "base_url": config["app"]["base_url"],
        },
        **result,
    }
    out = state / "verify.json"
    _write_json(out, report)
    coverage = result["coverage"]
    print(
        f"verify: {coverage['passed']}/{coverage['required']} PASS, "
        f"FAIL={coverage['failed']} UNKNOWN={coverage['unknown']} -> {out}"
    )
    return 0 if coverage.get("closed") else 2


def cmd_report(args: argparse.Namespace) -> int:
    root = _project(args.project)
    path = root / STATE_DIR / "verify.json"
    if not path.exists():
        print("no verification report; run `ui-agentic verify`", file=sys.stderr)
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    coverage = data["coverage"]
    print(f"subject: {data['subject']['project_digest']}")
    print(f"browser: {data['browser']}")
    print(f"coverage: {coverage['passed']}/{coverage['required']}")
    print(f"fail: {coverage['failed']}  unknown: {coverage['unknown']}")
    print(f"evidence_root: {data['evidence_root']}")
    return 0 if coverage.get("closed") else 2


def cmd_lock(args: argparse.Namespace) -> int:
    root = _project(args.project)
    path = root / STATE_DIR / "verify.json"
    if not path.exists():
        print("NO LOCK: verification report missing", file=sys.stderr)
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("coverage", {}).get("closed"):
        print("NO LOCK: required scenario set is not closed", file=sys.stderr)
        return 2
    print(
        "NO LOCK: external-project attestation is not implemented yet. "
        "Verification is valid as OBSERVED evidence only; do not claim LOCKED.",
        file=sys.stderr,
    )
    return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ui-agentic")
    parser.add_argument("--version", action="version", version=f"ui-agentic {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a project contract")
    init.add_argument("--project", default=".")
    init.add_argument("--base-url", default="http://127.0.0.1:3000")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    for name, help_text, func in (
        ("discover", "probe the declared routes", cmd_discover),
        ("verify", "compile and execute browser obligations", cmd_verify),
        ("report", "print the latest verification summary", cmd_report),
        ("lock", "attempt the final external-project lock gate", cmd_lock),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--project", default=".")
        command.set_defaults(func=func)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.func(args))
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
