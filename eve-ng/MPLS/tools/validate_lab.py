#!/usr/bin/env python3
"""Offline structural validation; does not launch Cisco IOSv."""
from collections import Counter
from pathlib import Path
import base64
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
FILES = ["MPLS-SP-Advanced.unl"] + [f"MPLS-SP-Advanced-AUTO-{s}.unl" for s in ("UNDERLAY","LDP","L3VPN")]
for filename in FILES:
    lab = ET.parse(ROOT / filename).getroot()
    nodes = lab.findall("./topology/nodes/node")
    networks = lab.findall("./topology/networks/network")
    assert len(nodes) == 16, (filename, "nodes")
    assert len(networks) == 23, (filename, "networks")
    ids = {n.get("id"): n.get("name") for n in nodes}
    netids = {n.get("id") for n in networks}
    assert len(ids) == 16 and len(netids) == 23
    assert len({n.get("uuid") for n in nodes}) == 16
    edges = Counter(i.get("network_id") for n in nodes for i in n.findall("interface"))
    assert set(edges) == netids and all(edges[n] == 2 for n in netids)
    configs = lab.findall("./objects/configs/config")
    if "-AUTO-" not in filename:
        assert not configs and all(n.get("config") == "0" for n in nodes)
    else:
        assert len(configs) == 16
        assert all(n.get("config") == "1" for n in nodes)
        assert {c.get("id") for c in configs} == set(ids)
        for cfg in configs:
            data = base64.b64decode(cfg.text, validate=True).decode("utf-8")
            assert f"hostname {ids[cfg.get('id')]}" in data
    print("PASS", filename, "16 routers, 23 links, ", len(configs), "startup configs")
