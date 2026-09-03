import pathlib
import tempfile
import unittest

from ui_agentic.app_adapter import HttpAppAdapter
from ui_agentic.config import ConfigError, load_config, project_digest, write_default_config


class ProductCliContractTests(unittest.TestCase):
    def test_init_round_trip_and_adapter_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_default_config(root, "http://127.0.0.1:3000")
            config = load_config(root)
            digest = project_digest(root)
            adapter = HttpAppAdapter(
                config["app"]["base_url"],
                digest,
                tuple(config["supported_domain"]["routes"]),
            )
            targets = adapter.targets()
            self.assertEqual(targets["/"].navigation_target, "http://127.0.0.1:3000/")
            self.assertEqual(len(targets["/"].code_digest), 12)

    def test_project_digest_ignores_state_and_generated_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "app.txt").write_text("v1")
            first = project_digest(root)
            (root / ".ui-agentic").mkdir()
            (root / ".ui-agentic" / "verify.json").write_text("volatile")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "x.js").write_text("volatile")
            self.assertEqual(first, project_digest(root))
            (root / "src" / "app.txt").write_text("v2")
            self.assertNotEqual(first, project_digest(root))

    def test_invalid_base_url_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            path = write_default_config(root, "http://127.0.0.1:3000")
            text = path.read_text().replace("http://127.0.0.1:3000", "localhost:3000")
            path.write_text(text)
            with self.assertRaises(ConfigError):
                load_config(root)


if __name__ == "__main__":
    unittest.main()
