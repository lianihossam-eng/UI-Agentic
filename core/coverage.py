"""Coverage Ledger, Evidence DAG, Measurement Readiness and Final Gate."""
import hashlib
import json

FINAL_GATE_KEYS = [
    "requirement_traceability",
    "required_proof_levels",
    "certificate_validation",
    "measurement_readiness",
    "critical_mutants_zero",
    "unstated_assumptions_zero",
    "regression_closed",
    "parent_contracts_valid",
    "state_transitions_complete",
    "cross_layer_invariants_complete",
    "compliance_obligations_complete",
    "visual_acceptance",
]


class CoverageLedger:
    def __init__(self, required):
        self.required_set = list(required)
        self.required = len(self.required_set)
        self.tested = 0
        self.passed = 0
        self.failed = 0
        self.unknown = 0
        self.results = []

    def record(self, result):
        self.results.append(result)
        self.tested += 1
        status = result.get("status", "UNKNOWN")
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.unknown += 1

    @property
    def coverage(self):
        return self.tested / self.required if self.required else 1.0

    def is_closed(self):
        return (
            self.tested == self.required
            and self.failed == 0
            and self.unknown == 0
        )

    def summary(self):
        return {
            "required": self.required,
            "tested": self.tested,
            "passed": self.passed,
            "failed": self.failed,
            "unknown": self.unknown,
            "coverage": self.coverage,
            "closed": self.is_closed(),
        }


class EvidenceDAG:
    def __init__(self):
        self.store = {}

    def key(self, code, contract, rule, scenario, browser, checker, environment=None):
        payload = [code, contract, rule, scenario, browser, checker, environment or {}]
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]

    def put(self, key, evidence):
        self.store[key] = evidence

    def get(self, key):
        return self.store.get(key)

    def root_digest(self):
        return hashlib.sha256(
            json.dumps(self.store, sort_keys=True).encode()
        ).hexdigest()[:16]


def measurement_readiness(page, require_app_ready=False):
    """Return PASS only when the rendered surface is measurably ready.

    No timeout/sleep can produce PASS. Missing required readiness evidence is UNKNOWN.
    """
    try:
        result = page.evaluate(
            """async (requireAppReady) => {
              if (document.fonts && document.fonts.ready) await document.fonts.ready;
              const appMarker = document.querySelector('[data-app-ready]');
              const appReady = appMarker ? appMarker.getAttribute('data-app-ready') === 'true' : null;
              const imagesReady = [...document.images].every(i => i.complete);
              const runningAnimations = document.getAnimations
                ? document.getAnimations().filter(a => a.playState === 'running').length
                : 0;
              const grid = document.querySelector('[data-testid="grid"], [data-testid="kpi-row"], [data-testid="main"]');
              let previous = null;
              let stableFrames = 0;
              for (let i = 0; i < 8 && stableFrames < 3; i++) {
                await new Promise(requestAnimationFrame);
                const r = grid?.getBoundingClientRect();
                const current = r ? [r.x, r.y, r.width, r.height].join(',') : 'missing';
                stableFrames = current === previous ? stableFrames + 1 : 0;
                previous = current;
              }
              return {
                readyState: document.readyState,
                fonts: document.fonts ? document.fonts.status : 'unsupported',
                imagesReady,
                runningAnimations,
                geometryStable: stableFrames >= 3,
                appMarkerPresent: !!appMarker,
                appReady,
                requireAppReady
              };
            }""",
            require_app_ready,
        )
    except Exception as exc:
        return {"status": "UNKNOWN", "reason": f"readiness-evaluation-error: {exc}"}

    blockers = []
    if result.get("readyState") != "complete":
        blockers.append("document-not-complete")
    if result.get("fonts") not in ("loaded", "unsupported"):
        blockers.append("fonts-not-loaded")
    if not result.get("imagesReady"):
        blockers.append("images-pending")
    if result.get("runningAnimations", 0) > 0:
        blockers.append("running-animations")
    if not result.get("geometryStable"):
        blockers.append("geometry-not-stable")
    if require_app_ready and result.get("appReady") is not True:
        blockers.append("app-readiness-unproven")

    return {
        "status": "PASS" if not blockers else "UNKNOWN",
        "checks": result,
        "blockers": blockers,
    }


def final_confirmation_gate(ledger, checks):
    """Fail closed: every canonical gate input must be explicitly True."""
    missing_or_failed = [key for key in FINAL_GATE_KEYS if checks.get(key) is not True]
    passed = ledger.is_closed() and not missing_or_failed
    return {
        "passed": passed,
        "coverage": ledger.summary(),
        "checks": {key: checks.get(key) for key in FINAL_GATE_KEYS},
        "blocking_gates": missing_or_failed,
    }
