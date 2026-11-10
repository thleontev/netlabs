#!/usr/bin/env python3
"""Проверка структуры MSTP Multi-Region без запуска EVE-NG."""
from pathlib import Path
from collections import defaultdict
import base64
import re
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
FILE = BASE / "MSTP-Multi-Region.unl"
NEEDED = {"SW1-1", "SW1-2", "SW1-3", "SW2-1", "SW2-2",
          "SW2-3", "SW3-1", "SW3-2", "SW3-3", "SW4"}
def test():
    root = ET.parse(FILE).getroot()
    nodes = root.findall("./topology/nodes/node")
    networks = root.findall("./topology/networks/network")
    assert len(nodes) == 10, f"Ожидалось 10 устройств, найдено {len(nodes)}"
    assert len(networks) == 17, f"Ожидалось 17 сетей, найдено {len(networks)}"
    assert {x.get("name") for x in nodes} == NEEDED
    ids = {x.get("id") for x in nodes}
    cfgs = {x.get("id"): x.text for x in root.findall("./objects/configs/config")}
    assert set(cfgs) == ids
    endpoints = defaultdict(list)
    for node in nodes:
        name = node.get("name")
        assert node.get("config") == "1", name
        content = base64.b64decode(cfgs[node.get("id")], validate=True).decode("ascii")
        assert re.search(r"^hostname " + re.escape(name) + r"$", content, re.M)
        assert "vlan 10\n" in content and "vlan 20\n" in content and "vlan 30\n" in content
        disk = (BASE / "configs" / (name + ".cfg")).read_text(encoding="ascii")
        assert content.strip() == disk.strip(), name
        if name != "SW4":
            region = "region" + name[2]
            assert "spanning-tree mode mst" in content
            assert " name " + region + "\n" in content
            assert " revision 1\n" in content
            assert " instance 1 vlan 10, 20, 30\n" in content
        else:
            assert "spanning-tree mode rapid-pvst" in content
            for port in ("GigabitEthernet0/0", "GigabitEthernet0/1"):
                assert port in content
        for port in node.findall("./interface"):
            endpoints[port.get("network_id")].append((name, port.get("name")))
    network_ids = {n.get("id") for n in networks}
    assert set(endpoints) == network_ids
    assert all(len(v) == 2 for v in endpoints.values())
    assert all(len(set(v)) == 2 for v in endpoints.values())
    print("OK: 10 устройств, 17 линков, 10 встроенных и дисковых конфигураций.")
    print("OK: MST region1/2/3, VLAN 10/20/30, SW4 Rapid-PVST.")
if __name__ == "__main__":
    try:
        test()
    except (AssertionError, ValueError, ET.ParseError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
