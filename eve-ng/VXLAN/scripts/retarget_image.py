#!/usr/bin/env python3
"""Retarget EVE QEMU folder names without changing interface mappings."""
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
p=argparse.ArgumentParser()
p.add_argument('unl',type=Path)
p.add_argument('--nxos',default=None,help='EVE QEMU image folder, e.g. nxosv9k-9300v-9.3.9')
p.add_argument('--linux',default=None,help='EVE QEMU image folder, e.g. linux-vxlan-debian12')
p.add_argument('--out',type=Path,default=None)
a=p.parse_args()
root=ET.parse(a.unl)
for node in root.findall('./topology/nodes/node'):
  if node.get('type')!='qemu':continue
  if node.get('template')=='nxosv9k' and a.nxos:node.set('image',a.nxos)
  if node.get('template')=='linux' and a.linux:node.set('image',a.linux)
out=a.out or a.unl.with_name(a.unl.stem+'-custom.unl')
root.write(out,encoding='utf-8',xml_declaration=True)
print(out)
