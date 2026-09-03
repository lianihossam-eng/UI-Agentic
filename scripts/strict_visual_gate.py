"""Independent fail-closed verifier for the visual acceptance contract."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = BASE / "reports"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
CONTRACT_VERSION = "visual-v3-exact-snapshot"
REQUIRED_STATES = {"default", "modal-open"}
EXPECTED_COUNT = 25


def fail(message: str) -> None:
    print(f"STRICT VISUAL FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def sha16_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


def file_sha16(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"cannot read {path.relative_to(BASE)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must be a JSON object")
    return value


def checker_digest() -> str:
    h = hashlib.sha256()
    for name in ("scripts/enforce_visual_contract.py", "scripts/strict_visual_gate.py"):
        h.update((BASE / name).read_bytes())
    return h.hexdigest()[:16]


def verify_report_hash(report: dict) -> None:
    expected = report.get("report_hash")
    if not expected:
        fail("visual_review missing report_hash")
    payload = {k: v for k, v in report.items() if k not in ("report_hash", "report_hash_algo")}
    if sha16_json(payload) != expected:
        fail("visual_review report_hash mismatch")


def main() -> int:
    visual = load(REPORT_DIR / "visual_review.json")
    approval_doc = load(REPORT_DIR / "visual_approval.json")
    current_run = load(REPORT_DIR / "current_run_evidence.json")

    verify_report_hash(visual)
    if visual.get("contract") != CONTRACT_VERSION:
        fail("visual contract version mismatch")
    if visual.get("visual_checker_digest") != checker_digest():
        fail("visual checker digest mismatch")
    if visual.get("screenshot_count") != EXPECTED_COUNT:
        fail(f"expected {EXPECTED_COUNT} screenshots")
    if set(visual.get("required_states") or []) != REQUIRED_STATES:
        fail("required visual states are incomplete")

    expected = visual.get("screenshot_digests")
    if not isinstance(expected, dict) or len(expected) != EXPECTED_COUNT:
        fail("screenshot digest manifest incomplete")
    actual = {}
    for name in sorted(expected):
        path = SCREENSHOT_DIR / name
        if not path.exists():
            fail(f"missing screenshot {name}")
        actual[name] = file_sha16(path)
    if actual != expected:
        fail("current screenshot bytes differ from visual_review manifest")

    digests_file = load(SCREENSHOT_DIR / "digests.json")
    if digests_file != actual:
        fail("digests.json differs from current screenshot bytes")
    snapshot = sha16_json(actual)
    if visual.get("snapshot_digest") != snapshot:
        fail("visual snapshot digest mismatch")
    if current_run.get("visual_snapshot_digest") != snapshot:
        fail("current_run_evidence visual snapshot mismatch")
    if current_run.get("visual_checker_digest") != checker_digest():
        fail("current_run_evidence visual checker mismatch")

    approvals = approval_doc.get("approvals")
    if approval_doc.get("contract") != CONTRACT_VERSION or not isinstance(approvals, list):
        fail("visual_approval contract/approvals invalid")
    matches = [a for a in approvals if isinstance(a, dict) and a.get("snapshot_digest") == snapshot]
    if len(matches) != 1:
        fail("exactly one approval for current snapshot is required")
    approval = matches[0]
    reviewer = str(approval.get("reviewer") or "")
    if approval.get("reviewer_type") != "agent" or not reviewer.startswith("agent:") or reviewer == "agent:":
        fail("reviewer must be an explicit agent identity; human identity cannot be inferred")
    if approval.get("reviewed_image_count") != EXPECTED_COUNT:
        fail("approval did not review the complete 25-image bundle")
    if approval.get("reviewed_images_digest") != snapshot:
        fail("approval image digest does not equal current snapshot")
    if set(approval.get("reviewed_states") or []) != REQUIRED_STATES:
        fail("approval does not cover default + modal-open states")
    if not approval.get("reviewed_at") or not approval.get("rubric"):
        fail("approval metadata incomplete")
    if approval.get("verdict") != "ACCEPTED":
        fail("current snapshot is not ACCEPTED")

    if visual.get("verdict") != "ACCEPTED" or visual.get("status") != "PASS":
        fail("visual_review is not PASS/ACCEPTED")
    if visual.get("reviewer") != reviewer or visual.get("reviewer_type") != "agent":
        fail("visual_review reviewer does not match current approval")
    if current_run.get("visual_accepted") is not True:
        fail("current_run_evidence does not mark visual accepted")

    print(
        "STRICT VISUAL PASS",
        json.dumps(
            {
                "snapshot": snapshot,
                "images": EXPECTED_COUNT,
                "states": sorted(REQUIRED_STATES),
                "reviewer": reviewer,
                "visual_checker_digest": checker_digest(),
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
