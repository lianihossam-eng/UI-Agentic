import pathlib
import unittest

import yaml

from core.attestation import attest, checker
from core.coverage import CoverageLedger, final_confirmation_gate
from core.scenario_compiler import MODAL_STATE_RULES, compile as compile_scenarios

BASE = pathlib.Path(__file__).resolve().parent.parent


class ProofGateTests(unittest.TestCase):
    def test_unknown_blocks_coverage_closure(self):
        ledger = CoverageLedger([{"rule": "a"}])
        ledger.record({"status": "UNKNOWN"})
        self.assertFalse(ledger.is_closed())

    def test_missing_final_gate_inputs_block_confirmation(self):
        ledger = CoverageLedger([{"rule": "a"}])
        ledger.record({"status": "PASS"})
        gate = final_confirmation_gate(ledger, {})
        self.assertFalse(gate["passed"])
        self.assertIn("measurement_readiness", gate["blocking_gates"])

    def test_attestation_refuses_failed_gate(self):
        with self.assertRaises(ValueError):
            attest(
                "build",
                "contract",
                "rules",
                "scenarios",
                "evidence",
                {"passed": False},
                {"browser": "test"},
            )

    def test_generic_attestation_is_never_locked(self):
        record = attest(
            "build",
            "contract",
            "rules",
            "scenarios",
            "evidence",
            {"passed": True},
            {"browser": "test"},
        )
        self.assertEqual(record["verdict"], "PROVISIONAL")
        self.assertNotEqual(record["verdict"], "LOCKED")

    def test_observed_sampling_is_not_certificate(self):
        observed = {
            "proof_level": "observed",
            "proof_source": "execution",
            "status": "PASS",
            "bound": 0.0,
            "tolerance": 0.5,
            "domain": [320, 1440],
        }
        self.assertFalse(checker(observed))

    def test_bounded_certificate_can_pass_checker(self):
        bounded = {
            "proof_level": "bounded",
            "proof_source": "model",
            "status": "PASS",
            "bound": 0.25,
            "tolerance": 0.5,
            "domain": [320, 1440],
        }
        self.assertTrue(checker(bounded))

    def _scenarios(self):
        domain = yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]
        return domain, compile_scenarios(domain)

    def test_compiler_emits_235_unique_obligations(self):
        _, scenarios = self._scenarios()
        ids = [scenario["scenario_id"] for scenario in scenarios]
        self.assertEqual(len(scenarios), 235)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(scenario["required_proof_level"] == "observed" for scenario in scenarios))

    def test_breakpoint_rule_is_required_for_every_default_route_viewport(self):
        domain, scenarios = self._scenarios()
        breakpoint = [
            scenario
            for scenario in scenarios
            if scenario["rule"] == "breakpoint.shell.direction" and scenario.get("state", "default") == "default"
        ]
        self.assertEqual(len(breakpoint), len(domain["routes"]) * len(domain["viewport_widths"]))
        self.assertEqual(len(breakpoint), 15)

    def test_modal_open_state_has_explicit_rule_matrix(self):
        domain, scenarios = self._scenarios()
        modal_state = [
            scenario
            for scenario in scenarios
            if scenario.get("state") == "modal-open" and scenario["rule"] in MODAL_STATE_RULES
        ]
        modal_routes = [
            route
            for route, states in domain["states_by_route"].items()
            if "modal-open" in states
        ]
        expected = len(MODAL_STATE_RULES) * len(modal_routes) * len(domain["viewport_widths"])
        self.assertEqual(expected, 70)
        self.assertEqual(len(modal_state), expected)
        self.assertEqual(len({scenario["scenario_id"] for scenario in modal_state}), expected)

    def test_modal_integrity_is_required_at_all_modal_viewports(self):
        domain, scenarios = self._scenarios()
        modal_integrity = [scenario for scenario in scenarios if scenario["rule"] == "MODAL_INTEGRITY"]
        self.assertEqual(len(modal_integrity), 10)
        self.assertEqual(
            {scenario["viewport"] for scenario in modal_integrity},
            set(domain["viewport_widths"]),
        )

    def test_transitions_are_executed_at_all_declared_viewports(self):
        domain, scenarios = self._scenarios()
        transitions = [scenario for scenario in scenarios if scenario["rule"].startswith("transition:")]
        self.assertEqual(len(transitions), 20)
        self.assertEqual(
            {scenario["viewport"] for scenario in transitions},
            set(domain["viewport_widths"]),
        )
        self.assertEqual(len({scenario["scenario_id"] for scenario in transitions}), 20)


if __name__ == "__main__":
    unittest.main()
