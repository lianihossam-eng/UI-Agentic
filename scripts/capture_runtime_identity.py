"""Capture the content-addressed runtime identity for the current proof run."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.runtime_identity import capture_runtime_identity

REPORT_DIR = BASE / "reports"


def fail(message: str) -> None:
    print(f"RUNTIME IDENTITY CAPTURE FAIL: {message}", file=sys.stderr)
    raise SystemExit(2)


def load(path: pathlib.Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except Exception as exc:
        fail(f"cannot read {path.relative_to(BASE)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(BASE)} must be an object")
    return value


def sha16_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    current = load(REPORT_DIR / "current_run_evidence.json")
    if current.get("generation_mode") != "current-run":
        fail("current_run_evidence is not current-run generated")
    run_id = str(os.environ.get("GITHUB_RUN_ID", "local"))
    if str(current.get("source_run_id")) != run_id:
        fail("current_run_evidence source_run_id mismatch")
    binding = current.get("binding") or {}
    required = {
        "commit_sha",
        "scenario_digest",
        "rules_digest",
        "checker_digest",
        "environment_manifest_digest",
        "evidence_root",
    }
    if not required.issubset(binding):
        fail("current_run_evidence binding is incomplete")

    runtime = capture_runtime_identity()
    report = {
        **runtime,
        **{key: binding[key] for key in required},
        "generation_mode": "current-run",
        "source_run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "PASS",
    }
    payload = {key: value for key, value in report.items() if key not in ("report_hash", "report_hash_algo")}
    report["report_hash"] = sha16_json(payload)
    report["report_hash_algo"] = "sha256:16"
    (REPORT_DIR / "runtime_identity.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print(
        "RUNTIME IDENTITY CAPTURED",
        json.dumps(
            {
                "root": report["runtime_identity_root"],
                "browser": report["browser"]["version"],
                "browser_sha256": report["browser"]["sha256"],
                "python_sha256": report["python"]["sha256"],
                "fonts": len(report["fonts"]),
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
