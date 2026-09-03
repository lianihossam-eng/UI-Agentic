import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile


class PackagingTests(unittest.TestCase):
    def test_wheel_contains_cli_and_verifier_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-deps",
                    "--no-build-isolation",
                    "--disable-pip-version-check",
                    "-w",
                    tmp,
                    ".",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            wheels = list(pathlib.Path(tmp).glob("ui_agentic-*.whl"))
            self.assertEqual(len(wheels), 1)
            with zipfile.ZipFile(wheels[0]) as archive:
                names = set(archive.namelist())
                self.assertIn("ui_agentic/cli.py", names)
                self.assertIn("core/replay_engine.py", names)
                self.assertIn("gvh/verify.py", names)
                entry_points = [name for name in names if name.endswith("entry_points.txt")]
                self.assertEqual(len(entry_points), 1)
                text = archive.read(entry_points[0]).decode("utf-8")
                self.assertIn("ui-agentic = ui_agentic.cli:main", text)


if __name__ == "__main__":
    unittest.main()
