"""Command-line interface for using UI-Agentic against another local project."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone
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
from ui_agentic.identity import contract_digest, verifier_identity
from ui_agentic.visual_review import VisualReviewError, capture_review_matrix

VERIFY_SCHEMA = "ui-agentic-external-verification-v2"
APPROVAL_SCHEMA = "ui-agentic-external-visual-approval-v1"


def _project(value: str | None) -> pathlib.Path:
    return pathlib.Path(value or ".").resolve()


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _with_artifact_hash(data: dict) -> dict:
    result = dict(data)
    result.pop("artifact_hash", None)
    result["artifact_hash_algo"] = "sha256"
    payload = {k: v for k, v in result.items() if k != "artifact_hash"}
    result["artifact_hash"] = _canonical_digest(payload)
    return result


def _artifact_hash_valid(data: dict) -> bool:
    expected = data.get("artifact_hash")
    if not isinstance(expected, str) or len(expected) != 64:
        return False
    payload = {k: v for k, v in data.items() if k != "artifact_hash"}
    return _canonical_digest(payload) == expected


def _write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_object(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigError(f"{path} must contain a JSON object")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
        "contract_digest": contract_digest(config),
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
    contract_root = contract_digest(config)
    verifier = verifier_identity()
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
        capture_screenshots=False,
    )
    visual = capture_review_matrix(
        domain=domain,
        route_targets=adapter.navigation_targets(),
        screenshot_dir=state / "screenshots",
    )
    if visual.get("browser") != result.get("browser"):
        raise VisualReviewError(
            f"browser mismatch between evidence and visual capture: "
            f"{result.get('browser')} != {visual.get('browser')}"
        )
    report = _with_artifact_hash(
        {
            "schema": VERIFY_SCHEMA,
            "generated_at": _utc_now(),
            "subject": {
                "type": "local-project",
                "project_root": str(source_root),
                "project_digest": source_digest,
            },
            "contract": {
                "contract_digest": contract_root,
                "supported_domain": domain,
            },
            "target": {
                "base_url": config["app"]["base_url"],
                "routes": adapter.navigation_targets(),
            },
            "verifier": verifier,
            "visual": visual,
            **result,
        }
    )
    out = state / "verify.json"
    _write_json(out, report)
    coverage = result["coverage"]
    print(
        f"verify: {coverage['passed']}/{coverage['required']} PASS, "
        f"FAIL={coverage['failed']} UNKNOWN={coverage['unknown']} -> {out}"
    )
    print(
        f"subject={source_digest[:16]} contract={contract_root[:16]} "
        f"verifier={verifier['verifier_digest'][:16]} "
        f"visual={visual['review_fingerprint_digest'][:16]}"
    )
    return 0 if coverage.get("closed") else 2


def cmd_report(args: argparse.Namespace) -> int:
    root = _project(args.project)
    path = root / STATE_DIR / "verify.json"
    if not path.exists():
        print("no verification report; run `ui-agentic verify`", file=sys.stderr)
        return 2
    data = _read_object(path)
    if not _artifact_hash_valid(data):
        print("verification report integrity failure", file=sys.stderr)
        return 2
    coverage = data["coverage"]
    print(f"subject: {data['subject']['project_digest']}")
    print(f"contract: {data['contract']['contract_digest']}")
    print(f"verifier: {data['verifier']['verifier_digest']}")
    print(f"browser: {data['browser']}")
    print(f"coverage: {coverage['passed']}/{coverage['required']}")
    print(f"fail: {coverage['failed']}  unknown: {coverage['unknown']}")
    print(f"evidence_root: {data['evidence_root']}")
    print(f"visual_snapshot: {data['visual']['snapshot_digest']}")
    print(f"visual_fingerprint: {data['visual']['review_fingerprint_digest']}")
    return 0 if coverage.get("closed") else 2


def cmd_review(args: argparse.Namespace) -> int:
    root = _project(args.project)
    verify_path = root / STATE_DIR / "verify.json"
    if not verify_path.exists():
        print("NO REVIEW: verification report missing", file=sys.stderr)
        return 2
    data = _read_object(verify_path)
    if not _artifact_hash_valid(data):
        print("NO REVIEW: verification report integrity failure", file=sys.stderr)
        return 2
    if not data.get("coverage", {}).get("closed"):
        print("NO REVIEW: required scenario set is not closed", file=sys.stderr)
        return 2
    reviewer = args.reviewer.strip()
    if not reviewer or ":" not in reviewer:
        print("NO REVIEW: --reviewer must be an explicit namespaced identity", file=sys.stderr)
        return 2
    verdict = "ACCEPTED" if args.accept else "REJECTED"
    visual = data["visual"]
    approval = _with_artifact_hash(
        {
            "schema": APPROVAL_SCHEMA,
            "verdict": verdict,
            "reviewer": reviewer,
            "reviewer_type": args.reviewer_type,
            "identity_assertion": "explicit-self-declared",
            "reviewed_at": _utc_now(),
            "rubric": args.rubric,
            "subject_project_digest": data["subject"]["project_digest"],
            "contract_digest": data["contract"]["contract_digest"],
            "verifier_digest": data["verifier"]["verifier_digest"],
            "reviewed_snapshot_digest": visual["snapshot_digest"],
            "review_fingerprint_algo": visual["review_fingerprint_algo"],
            "review_fingerprint_digest": visual["review_fingerprint_digest"],
            "reviewed_image_count": visual["image_count"],
            "reviewed_states": visual["states"],
        }
    )
    out = root / STATE_DIR / "visual-approval.json"
    _write_json(out, approval)
    print(
        f"visual review {verdict}: {visual['image_count']} images, "
        f"fingerprint={visual['review_fingerprint_digest']} -> {out}"
    )
    return 0 if verdict == "ACCEPTED" else 2


def _prelock_check(root: pathlib.Path) -> tuple[bool, list[str], dict | None]:
    blockers: list[str] = []
    verify_path = root / STATE_DIR / "verify.json"
    approval_path = root / STATE_DIR / "visual-approval.json"
    if not verify_path.exists():
        return False, ["verification-report-missing"], None
    data = _read_object(verify_path)
    if not _artifact_hash_valid(data):
        blockers.append("verification-report-integrity")
    if data.get("schema") != VERIFY_SCHEMA:
        blockers.append("verification-schema")
    if not data.get("coverage", {}).get("closed"):
        blockers.append("coverage-not-closed")

    config = load_config(root)
    source_root = resolve_source_root(root, config)
    if data.get("subject", {}).get("project_digest") != project_digest(source_root):
        blockers.append("subject-changed-since-verify")
    if data.get("contract", {}).get("contract_digest") != contract_digest(config):
        blockers.append("contract-changed-since-verify")
    current_verifier = verifier_identity()
    if data.get("verifier", {}).get("verifier_digest") != current_verifier["verifier_digest"]:
        blockers.append("verifier-changed-since-verify")

    if not approval_path.exists():
        blockers.append("visual-approval-missing")
    else:
        approval = _read_object(approval_path)
        if not _artifact_hash_valid(approval):
            blockers.append("visual-approval-integrity")
        if approval.get("verdict") != "ACCEPTED":
            blockers.append("visual-not-accepted")
        expected = {
            "subject_project_digest": data.get("subject", {}).get("project_digest"),
            "contract_digest": data.get("contract", {}).get("contract_digest"),
            "verifier_digest": data.get("verifier", {}).get("verifier_digest"),
            "reviewed_snapshot_digest": data.get("visual", {}).get("snapshot_digest"),
            "review_fingerprint_algo": data.get("visual", {}).get("review_fingerprint_algo"),
            "review_fingerprint_digest": data.get("visual", {}).get("review_fingerprint_digest"),
            "reviewed_image_count": data.get("visual", {}).get("image_count"),
            "reviewed_states": data.get("visual", {}).get("states"),
        }
        for field, value in expected.items():
            if approval.get(field) != value:
                blockers.append(f"visual-approval-binding:{field}")

    return not blockers, blockers, data


def cmd_lock(args: argparse.Namespace) -> int:
    root = _project(args.project)
    ready, blockers, data = _prelock_check(root)
    if not ready:
        print("NO LOCK: " + ", ".join(blockers), file=sys.stderr)
        return 2
    assert data is not None
    print(
        "NO LOCK: external pre-lock gates PASS, but authoritative external attestation "
        "is intentionally disabled until the Evidence DAG is bound to the external "
        "contract digest and the distributed verifier/runtime identity is independently "
        "attested. Do not claim LOCKED.",
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

    review = sub.add_parser("review", help="record explicit visual acceptance or rejection")
    review.add_argument("--project", default=".")
    choice = review.add_mutually_exclusive_group(required=True)
    choice.add_argument("--accept", action="store_true")
    choice.add_argument("--reject", action="store_true")
    review.add_argument("--reviewer", required=True)
    review.add_argument("--reviewer-type", choices=("agent", "human"), required=True)
    review.add_argument(
        "--rubric",
        default="no overflow; no collision; hierarchy coherent; declared states visually acceptable",
    )
    review.set_defaults(func=cmd_review)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.func(args))
    except (ConfigError, VisualReviewError) as exc:
        print(f"configuration/proof error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
