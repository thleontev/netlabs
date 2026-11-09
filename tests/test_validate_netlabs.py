"""Smoke tests for the dependency-free NetLabs validator."""

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / "tools" / "validate_netlabs.py"


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.lab = self.root / "eve-ng" / "IGP" / "DEMO"
        (self.lab / "configs").mkdir(parents=True)
        (self.lab / "docs").mkdir()
        (self.lab / "README.md").write_text("# Demo\n\n[Import](IMPORT-RU.md)\n", encoding="utf-8")
        (self.lab / "IMPORT-RU.md").write_text("# Import\n", encoding="utf-8")
        (self.lab / "docs" / "topology.png").write_bytes(b"fake preview")
        (self.lab / "configs" / "R1.cfg").write_text("hostname R1\nend\n", encoding="utf-8")
        self.put_unl()

    def put_unl(self, corrupt=False, dangling=False):
        payload = base64.b64encode(b"hostname R1\nend\n").decode()
        if corrupt:
            payload = "not-base64!"
        network = "19" if dangling else "10"
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<lab name="demo"><topology><nodes><node id="1" name="R1" config="1">
<interface id="0" network_id="{network}"/></node></nodes>
<networks><network id="10"/></networks></topology>
<objects><configs><config id="1">{payload}</config></configs></objects></lab>'''
        (self.lab / "demo.unl").write_text(xml, encoding="utf-8")

    def run_validator(self, *args):
        return subprocess.run([sys.executable, str(VALIDATOR), "--root", str(self.root),
                               "--lab", "eve-ng/IGP/DEMO", "--json", *args],
                              capture_output=True, text=True, check=False)

    def test_valid_unl(self):
        proc = self.run_validator()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["errors"], 0)

    def test_broken_base64_is_error(self):
        self.put_unl(corrupt=True)
        proc = self.run_validator()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Base64", proc.stdout)

    def test_dangling_network_is_error(self):
        self.put_unl(dangling=True)
        proc = self.run_validator()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("отсутствующую сеть", proc.stdout)

    def test_missing_markdown_link_is_warning_or_strict_error(self):
        (self.lab / "README.md").write_text("# Demo\n\n[Bad](missing.md)\n", encoding="utf-8")
        normal = self.run_validator()
        strict = self.run_validator("--strict-docs")
        self.assertEqual(normal.returncode, 0)
        self.assertGreater(json.loads(normal.stdout)["warnings"], 0)
        self.assertEqual(strict.returncode, 1)

    def test_gns3_dangling_node(self):
        project = self.root / "gns3" / "TEST"
        project.mkdir(parents=True)
        project_data = {"topology": {"nodes": [{"node_id": "ok"}],
                                     "links": [{"link_id": "bad", "nodes": [{"node_id": "lost"}]}]}}
        (project / "test.gns3").write_text(json.dumps(project_data), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(VALIDATOR), "--root", str(self.root),
                               "--lab", "gns3/TEST", "--json"], capture_output=True,
                              text=True, check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("отсутствующий узел", proc.stdout)


if __name__ == "__main__":
    unittest.main()
