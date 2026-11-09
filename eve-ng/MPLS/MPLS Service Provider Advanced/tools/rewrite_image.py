#!/usr/bin/env python3
"""Retarget the IOSv image in a selected .unl without stripping embedded config."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--image", required=True, help="Exact QEMU image directory name")
p.add_argument("--input", default="MPLS-SP-Advanced-AUTO-L3VPN.unl")
p.add_argument("--output", default="MPLS-SP-Advanced-AUTO-L3VPN-local.unl")
a = p.parse_args()
if "/" in a.image or "\\" in a.image or ".." in a.image:
    p.error("Image must be a folder name, not a path")
tree = ET.parse(ROOT / a.input)
for node in tree.getroot().findall("./topology/nodes/node"):
    node.set("image", a.image)
out = ROOT / a.output
tree.write(out, encoding="utf-8", xml_declaration=True)
print(out)
