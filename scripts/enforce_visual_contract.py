"""Build current-run visual evidence and apply fail-closed scene-bound approval.

Raw PNGs are always retained and hashed byte-for-byte.  Approval identity is the
rendered-scene fingerprint (DOM + visual computed style + geometry), not PNG
encoding/raster noise.  An approval therefore transfers only when the actual
rendered scene is identical under the declared fingerprint contract.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

from core.visual_scene import (
    capture_required_scene_manifest,
    expected_names,
    sha16_json as scene_sha16_json,
)

BASE = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = BASE / "reports"
SCREENSHOT_DIR = REPORT_DIR / "screenshots"
APPROVAL_PATH = REPORT_DIR / "visual_approval.json"
VISUAL_REPORT_PATH = REPORT_DIR / "visual_review.json"
CURRENT_RUN_PATH = REPORT_DIR / "current_run_evidence.json"
SCENE_MANIFEST_PATH = SCREENSHOT_DIR / "scene_digests.json"
RAW_MANIFEST_PATH = SCREENSHOT_DIR / "digests.json"

CONTRACT_VERSION = "visual-v4-scene-bound-snapshot"
SCENE_CONTRACT = "render-scene-v1"
REQUIRED_STATES = ("default", "modal-open")
EXPECTED_COUNT = 25


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
    for name in (
        "core/visual_scene.py",
        "scripts/enforce_visual_contract.py",
        "scripts/strict_visual_gate.py",
    ):
        path = BASE / name
        if path.exists():
            h.update(name.encode())
            h.update(path.read_bytes())
        else:
            h.update(f"missing:{name}".encode())
    return h.hexdigest()[:16]


def build_raw_manifest() -> dict[str, str]:
    expected = expected_names()
    actual = {p.name for p in SCREENSHOT_DIR.glob("*.png")}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeError(f"visual capture matrix mismatch missing={missing} extra={extra}")
    return {name: file_sha16(SCREENSHOT_DIR / name) for name in sorted(expected)}


def matching_approval(
    approval_doc: dict,
    scene_snapshot: str,
    raw_snapshot: str,
    image_count: int,
) -> tuple[str, dict | None, str]:
    if approval_doc.get("contract") != CONTRACT_VERSION:
        return "UNKNOWN", None, "approval-contract-mismatch"
    approvals = approval_doc.get("approvals")
    if not isinstance(approvals, list):
        return "UNKNOWN", None, "approvals-list-missing"

    matches = [
        item
        for item in approvals
        if isinstance(item, dict) and item.get("scene_snapshot_digest") == scene_snapshot
    ]
    if len(matches) != 1:
        return "UNKNOWN", None, "exactly-one-current-scene-approval-required"

    item = matches[0]
    reviewer = str(item.get("reviewer") or "")
    reviewer_type = item.get("reviewer_type")
    states = item.get("reviewed_states")
    reviewed_raw = str(item.get("reviewed_raw_snapshot_digest") or "")
    valid_identity = reviewer_type == "agent" and reviewer.startswith("agent:") and len(reviewer) > len("agent:")
    valid_scope = (
        item.get("reviewed_image_count") == image_count
        and item.get("reviewed_scene_digest") == scene_snapshot
        and len(reviewed_raw) == 16
        and isinstance(states, list)
        and set(states) == set(REQUIRED_STATES)
    )
    valid_metadata = bool(item.get("reviewed_at")) and bool(item.get("rubric"))
    verdict = item.get("verdict")

    if not valid_identity:
        return "UNKNOWN", item, "reviewer-must-be-explicit-agent-identity"
    if not valid_scope:
        return "UNKNOWN", item, "approval-scope-does-not-match-current-scene"
    if not valid_metadata:
        return "UNKNOWN", item, "approval-metadata-incomplete"
    if verdict == "ACCEPTED":
        reason = "scene-reviewed-and-accepted"
        if reviewed_raw != raw_snapshot:
            reason = "scene-equivalent-render-accepted"
        return "ACCEPTED", item, reason
    if verdict == "REJECTED":
        return "REJECTED", item, "scene-reviewed-and-rejected"
    return "UNKNOWN", item, "approval-verdict-not-final"


def main() -> int:
    # One browser pass produces both the semantic scene fingerprints and the exact
    # PNG audit artefacts.  A later strict checker independently recaptures scenes.
    scene_digests = capture_required_scene_manifest(SCREENSHOT_DIR)
    if len(scene_digests) != EXPECTED_COUNT:
        raise RuntimeError(f"expected {EXPECTED_COUNT} rendered scenes, got {len(scene_digests)}")
    SCENE_MANIFEST_PATH.write_text(json.dumps(scene_digests, indent=2, sort_keys=True))
    scene_snapshot = scene_sha16_json(scene_digests)

    raw_digests = build_raw_manifest()
    RAW_MANIFEST_PATH.write_text(json.dumps(raw_digests, indent=2, sort_keys=True))
    raw_snapshot = sha16_json(raw_digests)

    approval_doc = load_json(APPROVAL_PATH)
    verdict, approval, reason = matching_approval(
        approval_doc,
        scene_snapshot,
        raw_snapshot,
        len(raw_digests),
    )
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
            "scene_contract": SCENE_CONTRACT,
            "visual_checker_digest": visual_checker_digest(),
            "verdict": verdict,
            "status": status,
            "reason": reason,
            "reviewer": (approval or {}).get("reviewer"),
            "reviewer_type": (approval or {}).get("reviewer_type"),
            "reviewed_at": (approval or {}).get("reviewed_at"),
            "rubric": (approval or {}).get("rubric"),
            "approval_source": "reports/visual_approval.json",
            "approval_mode": "rendered-scene-equivalence",
            "reviewed_raw_snapshot_digest": (approval or {}).get("reviewed_raw_snapshot_digest"),
            "reference_images": (approval or {}).get("reference_images"),
            "current_images": "reports/screenshots/current-run",
            "screenshots_manifest": "reports/screenshots/digests.json",
            "scene_manifest": "reports/screenshots/scene_digests.json",
            "screenshot_count": len(raw_digests),
            "required_states": list(REQUIRED_STATES),
            "screenshot_digests": raw_digests,
            "scene_digests": scene_digests,
            "raw_snapshot_digest": raw_snapshot,
            "scene_snapshot_digest": scene_snapshot,
            # Keep the canonical downstream field, but its semantics are now the
            # deterministic rendered scene rather than nondeterministic PNG bytes.
            "snapshot_digest": scene_snapshot,
            "source": "25 exact PNGs plus 25 rendered-scene fingerprints from the current CI/browser run",
            "visual_gate_generated_at": utc_now(),
        }
    )
    write_report_hash(visual)
    VISUAL_REPORT_PATH.write_text(json.dumps(visual, indent=2, sort_keys=True))

    current_run = load_json(CURRENT_RUN_PATH)
    if not current_run:
        raise RuntimeError("current_run_evidence.json missing")
    current_run["visual_snapshot_digest"] = scene_snapshot
    current_run["visual_scene_digest"] = scene_snapshot
    current_run["visual_raw_snapshot_digest"] = raw_snapshot
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
                "scene_snapshot": scene_snapshot,
                "raw_snapshot": raw_snapshot,
                "images": len(raw_digests),
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
