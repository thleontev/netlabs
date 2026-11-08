#!/usr/bin/env python3
"""Check embedded EVE IOSv startup configurations against source .cfg files."""
from pathlib import Path
import xml.etree.ElementTree as ET
import base64
from embed_startup_configs import ROOT, STAGES, sanitize

def validate(stage, folder):
    path = ROOT / ("MPLS-SP-Advanced-AUTO-" + stage + ".unl")
    lab = ET.parse(path).getroot()
    nodes = lab.findall("./topology/nodes/node")
    configs = lab.findall("./objects/configs/config")
    ids = {n.get("id"): n.get("name") for n in nodes}
    assert len(nodes) == len(ids) == 16, (stage, "duplicate/missing node IDs")
    assert len(configs) == 16 and len({c.get("id") for c in configs}) == 16
    assert all(n.get("config") == "1" for n in nodes)
    assert len({n.get("uuid") for n in nodes}) == 16
    assert {c.get("id") for c in configs} == set(ids)
    for cfg in configs:
        name = ids[cfg.get("id")]
        raw = base64.b64decode(cfg.text, validate=True).decode("utf-8")
        expected = sanitize((ROOT / "configs" / folder / (name + ".cfg")).read_text(encoding="utf-8"))
        assert raw == expected, (stage, name, "startup payload differs from source")
        assert f"hostname {name}" in raw
        assert raw.strip().endswith("end")
    print("PASS", path.name, ": 16 nodes and 16 embedded startup configurations")

if __name__ == "__main__":
    for stage, folder in STAGES.items():
        validate(stage, folder)
