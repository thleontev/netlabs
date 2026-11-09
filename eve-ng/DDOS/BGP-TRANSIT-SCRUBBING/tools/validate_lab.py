#!/usr/bin/env python3
"""Offline structural checks, not a substitute for real EVE/IOSv boot tests."""
import base64
import csv
import ipaddress
import pathlib
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
lab = ET.parse(ROOT / "IP-TRANSIT-MULTIHOMING.unl")
nodes = lab.findall(".//topology/nodes/node")
bridges = lab.findall(".//topology/networks/network")
configs = {c.get("id"): c.text for c in lab.findall(".//objects/configs/config")}
assert len(nodes) == 11 and len(bridges) == 13
assert len({n.get("id") for n in nodes}) == 11
assert len({n.get("name") for n in nodes}) == 11
assert len({b.get("id") for b in bridges}) == 13
seen = Counter()
for node in nodes:
    ports = node.findall("interface")
    assert len({int(p.get("id")) for p in ports}) == len(ports)
    assert max(int(p.get("id")) for p in ports) < int(node.get("ethernet"))
    for port in ports:
        seen[port.get("network_id")] += 1
    if node.get("type") == "qemu":
        assert node.get("config") == "1" and node.get("id") in configs
        embedded = base64.b64decode(configs[node.get("id")], validate=True).decode("utf-8")
        external = (ROOT / "configs" / (node.get("name") + ".cfg")).read_text(encoding="utf-8")
        assert embedded == external, node.get("name")
        assert "hostname " + node.get("name") in embedded
    else:
        assert node.get("config") == "0"
assert set(seen) == {b.get("id") for b in bridges}
assert all(x == 2 for x in seen.values())
with (ROOT / "docs/LINKS.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 13
for row in rows:
    network = ipaddress.ip_network(row["subnet"])
    assert ipaddress.ip_address(row["address_a"]) in network
    assert ipaddress.ip_address(row["address_b"]) in network
    assert row["address_a"] != row["address_b"]
print("OK: 11 nodes, 13 links, 8 embedded IOSv startup configs, correct interface counts and IP plan")
print("NOTE: live EVE-NG routing behavior not tested.")
