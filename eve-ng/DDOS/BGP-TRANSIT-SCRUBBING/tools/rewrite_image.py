#!/usr/bin/env python3
"""Rewrite the QEMU vIOS image directory, leaving tracked .unl unchanged."""
import argparse
import pathlib
import re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
p = argparse.ArgumentParser()
p.add_argument("--image", required=True)
p.add_argument("--output", default="IP-TRANSIT-MULTIHOMING-local.unl")
a = p.parse_args()
if not re.fullmatch(r"vios-[A-Za-z0-9._-]+", a.image):
    p.error("--image must be the exact vios-* EVE QEMU folder")
source = ROOT / "IP-TRANSIT-MULTIHOMING.unl"
dest = ROOT / a.output
if dest.resolve() == source.resolve():
    p.error("Cannot overwrite tracked source .unl")
tree = ET.parse(source)
for node in tree.findall(".//node"):
    if node.get("type") == "qemu":
        node.set("image", a.image)
tree.write(dest, encoding="utf-8", xml_declaration=True)
print(dest)
