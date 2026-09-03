import unittest
from unittest.mock import patch

from core.coverage import EvidenceDAG, public_audit_contract_digest


class PublicAuditContractBindingTests(unittest.TestCase):
    def test_contract_digest_is_full_sha256(self):
        digest = public_audit_contract_digest()
        self.assertEqual(len(digest), 64)
        int(digest, 16)

    def test_legacy_contract_label_resolves_to_content_addressed_root(self):
        dag = EvidenceDAG()
        args = (
            "code",
            "contract-public-audit-v1",
            "rule",
            {"scenario_id": "s1"},
            "chromium@test",
            "checker",
            {"viewport": 320},
        )
        with patch("core.coverage.public_audit_contract_digest", return_value="a" * 64):
            first = dag.key(*args)
        with patch("core.coverage.public_audit_contract_digest", return_value="b" * 64):
            second = dag.key(*args)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
