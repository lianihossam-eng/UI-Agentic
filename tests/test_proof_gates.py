import unittest

from core.attestation import attest, checker
from core.coverage import CoverageLedger, final_confirmation_gate


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


if __name__ == "__main__":
    unittest.main()
