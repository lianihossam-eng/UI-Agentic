import copy
import pathlib
import tempfile
import unittest

from ui_agentic.config import default_config, project_digest
from ui_agentic.identity import contract_digest, verifier_digest, verifier_identity
from ui_agentic.visual_review import expected_names


class ExternalIdentityTests(unittest.TestCase):
    def test_contract_digest_tracks_normative_domain_not_base_url(self):
        config = default_config("http://127.0.0.1:3000")
        first = contract_digest(config)
        same_contract = copy.deepcopy(config)
        same_contract["app"]["base_url"] = "http://127.0.0.1:4000"
        self.assertEqual(first, contract_digest(same_contract))
        changed = copy.deepcopy(config)
        changed["supported_domain"]["viewport_widths"].append(1920)
        self.assertNotEqual(first, contract_digest(changed))

    def test_verifier_identity_is_content_addressed(self):
        identity = verifier_identity()
        self.assertEqual(len(identity["verifier_digest"]), 64)
        self.assertEqual(identity["verifier_digest"], verifier_digest())
        self.assertGreater(identity["source_files"], 0)
        self.assertEqual(len(identity["measurement_kernel_digest"]), 64)

    def test_visual_matrix_includes_every_declared_state(self):
        config = default_config()
        domain = config["supported_domain"]
        domain["routes"] = ["/", "/settings"]
        domain["viewport_widths"] = [320, 768]
        domain["states_by_route"] = {
            "/": ["default"],
            "/settings": ["default", "modal-open"],
        }
        self.assertEqual(
            expected_names(domain),
            {
                "root-320-default.png",
                "root-768-default.png",
                "settings-320-default.png",
                "settings-320-modal-open.png",
                "settings-768-default.png",
                "settings-768-modal-open.png",
            },
        )

    def test_project_digest_stays_independent_from_contract_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "app.js").write_text("console.log('app')")
            first = project_digest(root)
            (root / ".ui-agentic.yaml").write_text("version: 1\n")
            self.assertEqual(first, project_digest(root))


if __name__ == "__main__":
    unittest.main()
