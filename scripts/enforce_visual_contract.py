"""Build the complete current-run visual evidence bundle and apply fail-closed approval.

This script runs after capture_current_run_evidence.py. It extends the default-state
screenshots with modal-open states, computes one exact pixel snapshot digest over
all required images, and rewrites visual_review.json from a snapshot-specific
approval. No approval is transferable to a different snapshot.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import yaml
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = BASE / "reports"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
APPROVAL_PATH = REPORT_DIR / "visual_approval.json"
VISUAL_REPORT_PATH = REPORT_DIR / "visual_review.json"
CURRENT_RUN_PATH = REPORT_DIR / "current_run_evidence.json"

DOMAIN = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
ROUTE_FILE = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}
MODAL_ROUTES = ("/settings", "/analytics")
CONTRACT_VERSION = "visual-v3-exact-snapshot"
REQUIRED_STATES = ("default", "modal-open")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha16_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def file_sha16(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_json(path: pathlib.Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def write_report_hash(data: dict) -> None:
    payload = {k: v for k, v in data.items() if k not in ("report_hash", "report_hash_algo")}
    data["report_hash"] = sha16_json(payload)
    data["report_hash_algo"] = "sha256:16"


def visual_checker_digest() -> str:
    h = hashlib.sha256()
    for name in ("scripts/enforce_visual_contract.py", "scripts/strict_visual_gate.py"):
        path = BASE / name
        if path.exists():
            h.update(path.read_bytes())
        else:
            h.update(f"missing:{name}".encode())
    return h.hexdigest()[:16]


def default_name(route: str, viewport: int) -> str:
    return f"{route.strip('/')}-{viewport}.png"


def modal_name(route: str, viewport: int) -> str:
    return f"{route.strip('/')}-{viewport}-modal-open.png"


def expected_names() -> set[str]:
    names = {
        default_name(route, viewport)
        for route in DOMAIN["routes"]
        for viewport in DOMAIN["viewport_widths"]
    }
    names.update(
        modal_name(route, viewport)
        for route in MODAL_ROUTES
        for viewport in DOMAIN["viewport_widths"]
    )
    return names


def capture_modal_states() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for route in MODAL_ROUTES:
            for viewport in DOMAIN["viewport_widths"]:
                context = browser.new_context(
                    viewport={"width": viewport, "height": DOMAIN.get("viewport_height", 900)}
                )
                page = context.new_page()
                page.goto(ROUTE_FILE[route].as_uri())
                page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
                opener = page.locator('[data-testid="open-modal"]')
                if opener.count() != 1:
                    context.close()
                    raise RuntimeError(f"{route}@{viewport}: modal opener missing or ambiguous")
                opener.click()
                page.wait_for_function(
                    """() => {
                      const m=document.querySelector('[data-testid="modal"]');
                      if (!m) return false;
                      const s=getComputedStyle(m);
                      return m.hasAttribute('open') && s.display!=='none' && s.visibility!=='hidden';
                    }"""
                )
                page.screenshot(path=str(SCREENSHOT_DIR / modal_name(route, viewport)), full_page=True)
                context.close()
        browser.close()


def build_manifest() -> dict[str, str]:
    expected = expected_names()
    actual = {p.name for p in SCREENSHOT_DIR.glob("*.png")}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(f"visual capture matrix mismatch missing={missing} extra={extra}")
    return {name: file_sha16(SCREENSHOT_DIR / name) for name in sorted(expected)}


def matching_approval(approval_doc: dict, snapshot: str, image_count: int) -> tuple[str, dict | None, str]:
    if approval_doc.get("contract") != CONTRACT_VERSION:
        return "UNKNOWN", None, "approval-contract-mismatch"
    approvals = approval_doc.get("approvals")
    if not isinstance(approvals, list):
        return "UNKNOWN", None, "approvals-list-missing"
    matches = [a for a in approvals if isinstance(a, dict) and a.get("snapshot_digest") == snapshot]
    if len(matches) != 1:
        return "UNKNOWN", None, "exactly-one-current-snapshot-approval-required"
    item = matches[0]
    reviewer = str(item.get("reviewer") or "")
    reviewer_type = item.get("reviewer_type")
    states = item.get("reviewed_states")
    valid_identity = reviewer_type == "agent" and reviewer.startswith("agent:") and len(reviewer) > len("agent:")
    valid_scope = (
        item.get("reviewed_image_count") == image_count
        and item.get("reviewed_images_digest") == snapshot
        and isinstance(states, list)
        and set(states) == set(REQUIRED_STATES)
    )
    valid_metadata = bool(item.get("reviewed_at")) and bool(item.get("rubric"))
    verdict = item.get("verdict")
    if not valid_identity:
        return "UNKNOWN", item, "reviewer-must-be-explicit-agent-identity"
    if not valid_scope:
        return "UNKNOWN", item, "approval-scope-does-not-match-current-visual-bundle"
    if not valid_metadata:
        return "UNKNOWN", item, "approval-metadata-incomplete"
    if verdict == "ACCEPTED":
        return "ACCEPTED", item, "snapshot-reviewed-and-accepted"
    if verdict == "REJECTED":
        return "REJECTED", item, "snapshot-reviewed-and-rejected"
    return "UNKNOWN", item, "approval-verdict-not-final"


def main() -> int:
    capture_modal_states()
    digests = build_manifest()
    (SCREENSHOT_DIR / "digests.json").write_text(json.dumps(digests, indent=2, sort_keys=True))
    snapshot = sha16_json(digests)

    approval_doc = load_json(APPROVAL_PATH)
    verdict, approval, reason = matching_approval(approval_doc, snapshot, len(digests))
    status = "PASS" if verdict == "ACCEPTED" else ("FAIL" if verdict == "REJECTED" else "UNKNOWN")

    existing = load_json(VISUAL_REPORT_PATH)
    binding_fields = (
        "commit_sha",
        "scenario_digest",
        "rules_digest",
        "checker_digest",
        "environment_manifest_digest",
        "evidence_root",
        "generation_mode",
        "source_run_id",
        "generated_at",
    )
    visual = {k: existing.get(k) for k in binding_fields if k in existing}
    visual.update(
        {
            "contract": CONTRACT_VERSION,
            "visual_checker_digest": visual_checker_digest(),
            "verdict": verdict,
            "status": status,
            "reason": reason,
            "reviewer": (approval or {}).get("reviewer"),
            "reviewer_type": (approval or {}).get("reviewer_type"),
            "reviewed_at": (approval or {}).get("reviewed_at"),
            "rubric": (approval or {}).get("rubric"),
            "approval_source": "reports/visual_approval.json",
            "reference_images": "reports/screenshots/current-run",
            "screenshots_manifest": "reports/screenshots/digests.json",
            "screenshot_count": len(digests),
            "required_capture_matrix": {
                "default": {"routes": DOMAIN["routes"], "viewports": DOMAIN["viewport_widths"]},
                "modal-open": {"routes": list(MODAL_ROUTES), "viewports": DOMAIN["viewport_widths"]},
            },
            "required_states": list(REQUIRED_STATES),
            "screenshot_digests": digests,
            "snapshot_digest": snapshot,
            "source": "25 screenshots generated from the exact current CI/browser run",
            "visual_gate_generated_at": utc_now(),
        }
    )
    write_report_hash(visual)
    VISUAL_REPORT_PATH.write_text(json.dumps(visual, indent=2, sort_keys=True))

    current_run = load_json(CURRENT_RUN_PATH)
    if not current_run:
        raise RuntimeError("current_run_evidence.json missing")
    current_run["visual_snapshot_digest"] = snapshot
    current_run["visual_accepted"] = verdict == "ACCEPTED"
    current_run["visual_contract"] = CONTRACT_VERSION
    current_run["visual_checker_digest"] = visual["visual_checker_digest"]
    current_run.pop("artifact_hash", None)
    current_run["artifact_hash"] = sha16_json(current_run)
    CURRENT_RUN_PATH.write_text(json.dumps(current_run, indent=2, sort_keys=True))

    print(
        "STRICT VISUAL EVIDENCE GENERATED",
        json.dumps(
            {
                "snapshot": snapshot,
                "images": len(digests),
                "verdict": verdict,
                "reason": reason,
                "reviewer": visual.get("reviewer"),
                "checker": visual["visual_checker_digest"],
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
