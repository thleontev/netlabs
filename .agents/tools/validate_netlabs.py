#!/usr/bin/env python3
"""Offline NetLabs structural validator. Python stdlib only; never modifies files."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


@dataclass
class Finding:
    level: str
    path: str
    message: str


class Report:
    def __init__(self, root: Path, strict_docs: bool = False, strict_configs: bool = False):
        self.root = root
        self.strict_docs = strict_docs
        self.strict_configs = strict_configs
        self.findings: list[Finding] = []
        self.checked = 0

    def add(self, level: str, path: Path, message: str) -> None:
        if level == "WARN" and self.strict_docs and message.startswith("DOC:"):
            level = "ERROR"
        if level == "WARN" and self.strict_configs and message.startswith("CFG:"):
            level = "ERROR"
        try:
            rel = path.relative_to(self.root).as_posix()
        except ValueError:
            rel = str(path)
        self.findings.append(Finding(level, rel, message))

    def error(self, path: Path, message: str) -> None:
        self.add("ERROR", path, message)

    def warn(self, path: Path, message: str) -> None:
        self.add("WARN", path, message)


LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\n)]+)\)")


def check_markdown(md: Path, report: Report) -> None:
    text = md.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        report.warn(md, "DOC: пустой Markdown-файл")
        return
    text = re.sub(r"(?ms)^\s*(\`{3,}|~{3,})[^\n]*\n.*?^\s*\1[^\n]*$", "", text)
    for match in LINK.finditer(text):
        raw = match.group(1).strip().split(' "', 1)[0].strip("<>")
        if not raw or raw.startswith("#") or raw.startswith("{"):
            continue
        if urlsplit(raw).scheme or raw.startswith("//"):
            continue
        target = unquote(raw.split("#", 1)[0].split("?", 1)[0])
        if not target:
            continue
        resolved = (md.parent / target).resolve()
        if not resolved.is_relative_to(report.root):
            report.warn(md, f"DOC: ссылка выходит за пределы репозитория: {raw}")
        elif not resolved.exists():
            report.warn(md, f"DOC: отсутствует цель ссылки: {raw}")


def check_unl(path: Path, report: Report) -> None:
    report.checked += 1
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        report.error(path, f"UNL: некорректный XML: {exc}")
        return
    nodes = root.findall("./topology/nodes/node")
    networks = root.findall("./topology/networks/network")
    configs = root.findall("./objects/configs/config")
    if not nodes:
        report.error(path, "UNL: в топологии нет узлов")
    node_ids = [n.get("id") for n in nodes]
    net_ids = [n.get("id") for n in networks]
    cfg_ids = [c.get("id") for c in configs]
    for label, ids in (("node", node_ids), ("network", net_ids), ("config", cfg_ids)):
        if None in ids or len(ids) != len(set(ids)):
            report.error(path, f"UNL: пустые или дублирующиеся {label} ID")
    net_set = set(net_ids)
    node_set = set(node_ids)
    cfg_by_id = {c.get("id"): c for c in configs}
    for node in nodes:
        name = node.get("name") or f"node_{node.get('id')}"
        for iface in node.findall("interface"):
            net = iface.get("network_id")
            if net and net not in net_set:
                report.error(path, f"UNL: {name} — интерфейс ссылается на отсутствующую сеть {net}")
        if node.get("config") == "1" and node.get("id") not in cfg_by_id:
            report.error(path, f"UNL: {name} — config=1, но startup-config отсутствует")
    for config in configs:
        ident = config.get("id")
        if ident not in node_set:
            report.error(path, f"UNL: startup-config для отсутствующего узла {ident}")
            continue
        node = next((n for n in nodes if n.get("id") == ident), None)
        name = (node.get("name") if node is not None else None) or str(ident)
        try:
            payload = base64.b64decode((config.text or "").strip(), validate=True)
        except (binascii.Error, ValueError) as exc:
            report.error(path, f"UNL: {name} — неверная Base64-конфигурация: {exc}")
            continue
        if not payload:
            report.warn(path, f"CFG: {name} — пустой встроенный startup-config")
        if node is not None and node.get("config") != "1":
            report.warn(path, f"CFG: {name} — конфигурация встроена, но config не равен 1")
        standalone = path.parent / "configs" / f"{name}.cfg"
        if standalone.is_file() and standalone.read_bytes().replace(b"\r\n", b"\n").strip() != payload.replace(b"\r\n", b"\n").strip():
            report.warn(path, f"CFG: {name} — встроенный startup-config отличается от {standalone.relative_to(path.parent)}; проверьте платформенное преобразование")
    for cfg in (path.parent / "configs").glob("*.cfg"):
        if cfg.stat().st_size == 0:
            report.warn(cfg, "CFG: пустая конфигурация; объясните, если это предусмотрено лабораторией")


def check_gns3(path: Path, report: Report) -> None:
    report.checked += 1
    try:
        project = json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        report.error(path, f"GNS3: некорректный JSON: {exc}")
        return
    topology = project.get("topology")
    if not isinstance(topology, dict):
        report.error(path, "GNS3: отсутствует topology")
        return
    nodes = topology.get("nodes", [])
    links = topology.get("links", [])
    if not isinstance(nodes, list) or not isinstance(links, list):
        report.error(path, "GNS3: nodes/links имеют неверный формат")
        return
    ids = [n.get("node_id") for n in nodes if isinstance(n, dict)]
    if None in ids or len(ids) != len(set(ids)):
        report.error(path, "GNS3: отсутствующие или дублирующиеся node_id")
    known = set(ids)
    for link in links:
        if not isinstance(link, dict):
            report.error(path, "GNS3: неверный объект связи")
            continue
        for endpoint in link.get("nodes", []):
            if not isinstance(endpoint, dict) or endpoint.get("node_id") not in known:
                report.error(path, f"GNS3: связь {link.get('link_id', '?')} указывает на отсутствующий узел")


def check_lab(directory: Path, report: Report) -> None:
    if not directory.is_dir():
        report.error(directory, "LAB: каталог не найден")
        return
    unls = sorted(directory.glob("*.unl"))
    gns3s = sorted(directory.glob("*.gns3"))
    if not unls and not gns3s:
        report.warn(directory, "DOC: в каталоге нет файлов .unl/.gns3")
    for unl in unls:
        check_unl(unl, report)
    for project in gns3s:
        check_gns3(project, report)
    readme = directory / "README.md"
    if not readme.is_file():
        report.warn(directory, "DOC: отсутствует README.md (для исторических GNS3 — рекомендация)")
    for md in directory.rglob("*.md"):
        check_markdown(md, report)
    if unls:
        if not (directory / "IMPORT-RU.md").is_file():
            report.warn(directory, "DOC: отсутствует IMPORT-RU.md")
        images = list(directory.rglob("*.png"))
        if not images:
            report.warn(directory, "DOC: отсутствует PNG-схема топологии")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="корень репозитория")
    parser.add_argument("--lab", type=Path, action="append", help="путь к лаборатории относительно --root; можно повторять")
    parser.add_argument("--all", action="store_true", help="проверить все лаборатории EVE-NG/GNS3")
    parser.add_argument("--strict-docs", action="store_true", help="считать предупреждения DOC ошибками")
    parser.add_argument("--strict-configs", action="store_true", help="считать предупреждения CFG ошибками")
    parser.add_argument("--json", action="store_true", help="выдать машиночитаемый отчёт")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("корень репозитория не найден")
    report = Report(root, args.strict_docs, args.strict_configs)
    labs: set[Path] = set()
    if args.all or not args.lab:
        for platform in ("eve-ng", "gns3"):
            parent = root / platform
            if parent.is_dir():
                labs.update(p.parent for pattern in ("*.unl", "*.gns3") for p in parent.rglob(pattern))
    if args.lab:
        for lab in args.lab:
            dest = (root / lab).resolve()
            if not dest.is_relative_to(root):
                parser.error(f"путь за пределами --root: {lab}")
            labs.add(dest)
    for lab in sorted(labs):
        check_lab(lab, report)
    errors = sum(f.level == "ERROR" for f in report.findings)
    warnings = sum(f.level == "WARN" for f in report.findings)
    if args.json:
        print(json.dumps({"checked_projects": report.checked, "labs": len(labs), "errors": errors,
                          "warnings": warnings, "findings": [asdict(f) for f in report.findings]},
                         ensure_ascii=False, indent=2))
    else:
        for finding in report.findings:
            print(f"{finding.level}: {finding.path}: {finding.message}")
        print(f"Проверено лабораторий: {len(labs)}, проектов: {report.checked}; ошибок: {errors}; предупреждений: {warnings}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
