#!/usr/bin/env python3
"""Regenerate EVE-NG .unl files with embedded IOSv startup-config (stdlib only)."""
import argparse
import base64
import uuid
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = uuid.UUID("4ad7e389-6b30-5a07-a900-a28fd1de9ac0")
STAGES = {"UNDERLAY": "00-underlay", "LDP": "01-ldp", "L3VPN": "02-l3vpn"}

def sanitize(s):
    lines = s.replace("\r\n", "\n").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and lines[0].strip().lower() in ("enable", "configure terminal", "conf t"):
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or not lines[0].startswith("hostname "):
        raise ValueError("Missing hostname in source .cfg")
    if any(x.strip().lower() in ("enable", "configure terminal", "conf t") for x in lines):
        raise ValueError("Interactive CLI command found in startup configuration")
    if lines[-1] != "end":
        lines.append("end")
    return "! MPLS-SP-Advanced generated Cisco IOSv startup-config\n" + "\n".join(lines) + "\n"

def build(stage, folder, image=None):
    tree = ET.parse(ROOT / "MPLS-SP-Advanced.unl")
    lab = tree.getroot()
    lab.set("name", f"MPLS-SP-Advanced-{stage}-AUTO")
    lab.set("id", str(uuid.uuid5(NS, "mpls-sp-advanced-" + stage)))
    lab.set("description", f"{stage}: OSPF/MPLS/BGP staged config (16 embedded IOSv startup-configs)")
    nodes = lab.findall("./topology/nodes/node")
    configs = lab.find("./objects/configs")
    if configs is None:
        raise ValueError("Missing <objects><configs>")
    configs.clear()
    if len(nodes) != 16:
        raise ValueError(f"Expected 16 routers, found {len(nodes)}")
    for node in nodes:
        name = node.get("name")
        node.set("config", "1")
        node.set("uuid", str(uuid.uuid5(NS, stage + "/" + name)))
        if image:
            node.set("image", image)
        raw = (ROOT / "configs" / folder / (name + ".cfg")).read_text(encoding="utf-8")
        cfg = sanitize(raw)
        ET.SubElement(configs, "config", {"id": node.get("id")}).text = base64.b64encode(cfg.encode("utf-8")).decode("ascii")
    ET.indent(tree, space="  ")
    out = ROOT / ("MPLS-SP-Advanced-AUTO-" + stage + ".unl")
    tree.write(out, encoding="UTF-8", xml_declaration=True)
    print("Generated", out, len(nodes), "nodes, ", len(configs), "startup configs")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=[*STAGES, "ALL"], default="ALL")
    p.add_argument("--image", help="Exact folder name from /opt/unetlab/addons/qemu/")
    a = p.parse_args()
    for stage, folder in STAGES.items():
        if a.stage in ("ALL", stage):
            build(stage, folder, a.image)
