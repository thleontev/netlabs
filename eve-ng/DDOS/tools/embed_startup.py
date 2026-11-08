#!/usr/bin/env python3
"""Rebuild embedded startup-config entries inside the existing EVE-NG UNL."""
from pathlib import Path
import base64
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "CURATOR-BGP-MULTIAS-V3.unl"

def rebuild():
    tree = ET.parse(LAB)
    lab = tree.getroot()
    nodes = lab.findall("./topology/nodes/node")
    objects = lab.find("objects")
    if objects is None:
        objects = ET.SubElement(lab, "objects")
    configs = objects.find("configs")
    if configs is not None:
        objects.remove(configs)
    configs = ET.SubElement(objects, "configs")
    total = 0
    for node in nodes:
        if node.get("template") != "vios":
            node.set("config", "0")
            continue
        name = node.get("name")
        path = ROOT / "configs" / f"{name}.cfg"
        raw = path.read_bytes()
        if not raw.strip() or b"hostname " + name.encode() not in raw:
            raise ValueError(f"{name}: empty or incorrect configuration")
        node.set("config", "1")
        ET.SubElement(configs, "config", {"id": node.get("id")}).text = base64.b64encode(raw).decode("ascii")
        total += 1
    if total != 11:
        raise ValueError(f"Expected 11 routers, got {total}")
    ET.indent(tree, space="  ")
    tree.write(LAB, encoding="utf-8", xml_declaration=True)
    print(f"Updated {LAB} with {total} embedded IOSv startup configurations.")

if __name__ == "__main__":
    rebuild()
