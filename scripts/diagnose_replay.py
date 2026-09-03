"""Print exact failing/unknown obligations from one current checkout replay.

Diagnostic only: this script cannot create or modify proof reports and is never
accepted as evidence. It exists so a coverage failure is actionable by exact
scenario_id rather than only aggregate counters.
"""
from __future__ import annotations

import json
import pathlib
import sys

import yaml

BASE = pathlib.Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from core.replay_engine import replay
from core.scenario_compiler import compile as compile_scenarios

DOMAIN = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
SCENARIOS = compile_scenarios(DOMAIN)
ROUTE_FILES = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}


def main() -> int:
    result = replay(
        domain=DOMAIN,
        scenarios=SCENARIOS,
        route_files=ROUTE_FILES,
        capture_screenshots=False,
    )
    failures = []
    for record in result["records"]:
        status = (record.get("result") or {}).get("status", "UNKNOWN")
        if status != "PASS":
            failures.append(
                {
                    "scenario_id": (record.get("scenario") or {}).get("scenario_id"),
                    "rule": (record.get("scenario") or {}).get("rule"),
                    "route": (record.get("scenario") or {}).get("route"),
                    "viewport": (record.get("scenario") or {}).get("viewport"),
                    "state": (record.get("scenario") or {}).get("state", "default"),
                    "status": status,
                    "reason": (record.get("result") or {}).get("reason"),
                    "result": record.get("result"),
                }
            )
    print(
        "REPLAY DIAGNOSTIC",
        json.dumps(
            {
                "coverage": result["coverage"],
                "evidence_root": result["evidence_root"],
                "failure_count": len(failures),
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
