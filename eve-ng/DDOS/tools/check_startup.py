#!/usr/bin/env python3
"""Fail closed if startup-configs are absent, mismatched, or corrupt."""
from pathlib import Path
import base64
import binascii
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "CURATOR-BGP-MULTIAS-V3.unl"

def check():
    lab = ET.parse(LAB).getroot()
    nodes = lab.findall("./topology/nodes/node")
    routers = [n for n in nodes if n.get("type") == "qemu" and n.get("template") == "vios"]
    configs = lab.findall("./objects/configs/config")
    assert len(routers) == 11, f"Expected 11 IOSv routers; found {len(routers)}"
    assert len(configs) == 11, f"Expected 11 embedded configs; found {len(configs)}"
    config_by_id = {c.get("id"): c for c in configs}
    assert len(config_by_id) == 11, "Duplicate configuration IDs"
    for n in routers:
        name, ident = n.get("name"), n.get("id")
        assert n.get("config") == "1", f"{name}: startup config not enabled"
        assert ident in config_by_id, f"{name}: no embedded config"
        try:
            actual = base64.b64decode(config_by_id[ident].text or "", validate=True)
        except binascii.Error as error:
            raise AssertionError(f"{name}: broken base64: {error}")
        expected = (ROOT / "configs" / f"{name}.cfg").read_bytes()
        assert actual == expected, f"{name}: embedded config differs from configs/{name}.cfg"
    for n in nodes:
        if n not in routers:
            assert n.get("config") == "0", f"{n.get('name')}: unsupported VPCS startup flag"
    print(f"OK: {len(nodes)} nodes, {len(routers)} embedded IOSv startup-configs, exact byte match")
    print("Static check only: EVE-NG boot and BGP convergence have not been tested")

if __name__ == "__main__":
    check()
