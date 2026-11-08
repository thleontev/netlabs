#!/usr/bin/env python3
"""Replace EVE-NG QEMU image directory in all nodes without changing topology."""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description='Retarget .unl to your locally installed vios image directory')
p.add_argument('--image',required=True,help='Exact folder name from /opt/unetlab/addons/qemu/')
p.add_argument('--output',default='MPLS-SP-Advanced-local.unl')
a=p.parse_args()
assert '/' not in a.image and '\\' not in a.image and '..' not in a.image, 'image should be a folder name'
tree=ET.parse(ROOT/'MPLS-SP-Advanced.unl')
for node in tree.getroot().find('topology').find('nodes').findall('node'):
    node.set('image',a.image)
out=ROOT/a.output
tree.write(out,encoding='utf-8',xml_declaration=True)
print(out)
