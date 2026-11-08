#!/usr/bin/env python3
"""Static checks only: not NX-OS runtime or EVE boot validation."""
from pathlib import Path
from collections import Counter
from xml.etree import ElementTree as ET
root=Path(__file__).resolve().parents[1]
for file,expected in [('VXLAN-FABRIC-5N-6H.unl',12),('VXLAN-FABRIC-MULTITENANT-FW.unl',14)]:
 lab=ET.parse(root/file).getroot()
 assert lab.tag=='lab', file
 nodes=lab.findall('./topology/nodes/node')
 nets=lab.findall('./topology/networks/network')
 assert len(nets)==expected,(file,len(nets))
 assert len(nodes)==(12 if expected==14 else 11),(file,len(nodes))
 ids=[int(n.get('id')) for n in nets]
 assert len(set(ids))==len(ids),(file,'duplicate net id')
 ports={}
 used=Counter()
 for n in nodes:
  pairs=[int(i.get('id')) for i in n.findall('interface')]
  assert len(pairs)==len(set(pairs)),(file,n.get('name'),'duplicate port')
  for i in n.findall('interface'):
   assert int(i.get('network_id')) in ids
   used[int(i.get('network_id'))]+=1
   if n.get('template')=='nxosv9k':assert 1<=int(i.get('id'))<=6
  ports[n.get('name')]=pairs
 assert all(v==2 for v in used.values()),(file,used)
 for node in ['SPINE-01','SPINE-02','LEAF-01','LEAF-02','LEAF-03']:
  assert node in ports
for stage in ['00-underlay','01-evpn-l2','02-symmetric-irb','03-multitenancy-fw']:
 for node in ['SPINE-01','SPINE-02','LEAF-01','LEAF-02','LEAF-03']:
  s=(root/'configs'/stage/(node+'.cfg')).read_text()
  assert 'router ospf UNDERLAY' in s
  assert s.count('ip router ospf UNDERLAY')>= (4 if node.startswith('LEAF') else 4)
  if stage!='00-underlay':
   assert 'router bgp 65000' in s
   assert 'address-family l2vpn evpn' in s
  if stage!='00-underlay' and node.startswith('LEAF'):
   assert len([vni for vni in [10010,10020,10030] if f'member vni {vni}' in s])==2
   assert 'ingress-replication protocol bgp' in s
  if stage in ['02-symmetric-irb','03-multitenancy-fw'] and node.startswith('LEAF'):
   assert 'fabric forwarding anycast-gateway-mac' in s
   assert 'advertise l2vpn evpn' in s
   assert any(f'interface Vlan{v}' in s for v in [10,20,30])
  if stage=='03-multitenancy-fw' and node.startswith('LEAF'):
   for name in ['CLIENTS','APPS']:assert f'vrf context {name}' in s
for stage in ['01-evpn-l2','02-symmetric-irb','03-multitenancy-fw']:
 t=(root/'configs'/stage/'VPCS-commands.txt').read_text()
 assert t.count('\nip 192.168.')==6
 assert t.count('\nsave')==6
print('OK: UNL links, unique interfaces, VPCS commands, base OSPF, EVPN and VRF sections pass static validation')
