import importlib
import pathlib
import tomllib
import unittest


class PackagingTests(unittest.TestCase):
    def test_console_entry_point_and_packages_are_declared(self):
        data = tomllib.loads(pathlib.Path("pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["version"], "0.3.0")
        self.assertEqual(
            data["project"]["scripts"]["ui-agentic"],
            "ui_agentic.cli:main",
        )
        include = set(data["tool"]["setuptools"]["packages"]["find"]["include"])
        self.assertTrue({"ui_agentic*", "core*", "gvh*"}.issubset(include))
        module = importlib.import_module("ui_agentic.cli")
        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
