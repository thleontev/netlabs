#!/usr/bin/env python3
"""Static UNL / IOSv cross-check. Does not pretend to run Cisco images."""
import ipaddress
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from build_lab import R,V,NETS

def check(path):
 root=ET.parse(path).getroot()
 assert root.tag=='lab' and root.get('version')=='2'
 nodes=root.findall('./topology/nodes/node')
 assert len(nodes)==15,(len(nodes),'Expected 11 IOSv + 4 endpoints')
 assert len(set(n.get('id') for n in nodes))==15
 assert len(set(n.get('uuid') for n in nodes))==15
 nets=root.findall('./topology/networks/network')
 assert len(nets)==16
 network_ids={n.get('id') for n in nets}
 assert len(network_ids)==16
 bridge_endpoints=defaultdict(list)
 for n in nodes:
  assert n.get('config')=='0', (n.get('name'),'config missing')
  assert n.get('name') in R or n.get('name') in V
  for port in n.findall('interface'):
   assert port.get('network_id') in network_ids
   bridge_endpoints[port.get('network_id')].append((n.get('name'), port.get('id')))
 for bridge, ends in bridge_endpoints.items():
  assert len(ends)==2, (bridge,ends)
 for n in R:
  assert any(node.get('name')==n for node in nodes)
 conf={p.stem:p.read_text() for p in (ROOT/'configs').glob('*.cfg')}
 assert set(conf)==set(R), ('Wrong configs',set(conf)^set(R))
 # All physical interfaces: IPs on opposite ends must share exactly one /30 network.
 interface_ips={}
 for name,c in conf.items():
  parts=re.split(r'(?=^interface )',c,flags=re.M)
  for p in parts:
   m=re.match(r'interface (\S+)',p)
   if not m or not m.group(1).startswith('GigabitEthernet'):continue
   adr=re.search(r'ip address (\S+) (\S+)',p)
   assert adr,(name,m.group(1))
   interface_ips[(name,m.group(1).split('0/')[-1])]=ipaddress.IPv4Interface(f'{adr.group(1)}/{adr.group(2)}')
 for bridge, ends in bridge_endpoints.items():
  if not all((n,i) in interface_ips for n,i in ends): continue
  ips=[interface_ips[x] for x in ends]
  assert ips[0].network == ips[1].network and ips[0].ip != ips[1].ip, (bridge, ends, ips)
 # ASN and BGP peer IPs are reciprocal on physical links and tunnels.
 asn={name:int(re.search(r'router bgp (\d+)',c).group(1)) for name,c in conf.items() if 'router bgp ' in c}
 peers={}
 for name,c in conf.items():
  peers[name]={ip:int(remote) for ip,remote in re.findall(r'^ neighbor (\d+\.\d+\.\d+\.\d+) remote-as (\d+)$',c,re.M)}
 phys_ips={str(ip.ip):name for (name,_),ip in interface_ips.items()}
 overlay_ips={'172.31.1.1':'R-CUR1','172.31.1.2':'R-CE','172.31.2.1':'R-CUR2','172.31.2.2':'R-CE','198.18.0.21':'R-CUR1','198.18.0.22':'R-CUR2','198.19.0.200':'R-CUR-RR'}
 all_ips=phys_ips | overlay_ips
 for name,allpeers in peers.items():
  for address,remote_as in allpeers.items():
   assert address in all_ips,(name,'Peer missing',address)
   other=all_ips[address]
   assert asn[other]==remote_as,(name,address,other,remote_as)
   assert any(v==asn[name] for k,v in peers[other].items() if all_ips.get(k)==name), (name,'Nonreciprocal BGP neighbor',other)
 # No unintentional /24 leakage directly from CE to ISP in baseline.
 ce=conf['R-CE']
 assert 'neighbor 198.18.11.1 prefix-list DENY-ALL out' in ce
 assert 'neighbor 198.18.12.1 prefix-list DENY-ALL out' in ce
 assert 'neighbor 172.31.1.1 prefix-list PROTECTED out' in ce
 assert 'neighbor 172.31.2.1 prefix-list PROTECTED out' in ce
 assert 'ip route 198.18.0.21 255.255.255.255 198.18.11.1' in ce
 assert 'ip route 198.18.0.22 255.255.255.255 198.18.12.1' in ce
 for pop in ('R-CUR1','R-CUR2'):
  text=conf[pop]
  assert 'SCRUB-POLICY in' in text
  assert 'neighbor 198.19.0.200 next-hop-self' in text
  assert 'router ospf 20' in text
  assert 'ip prefix-list POP-LOCAL seq 5 permit 198.18.0.' in text
 rr=conf['R-CUR-RR']
 assert rr.count('route-reflector-client')==2
 assert 'router ospf 20' in rr
 print('PASS:',len(nodes),'nodes,',len(nets),'bridges; per-node config; /30 link addressing; eBGP + iBGP reciprocity; two GRE, OSPF/RR, baseline no-bypass policy')
 print('STATIC VALIDATION ONLY: no EVE runtime, IOS boot, or packet forwarding tests performed')

if __name__=='__main__':
 path=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'CURATOR-BGP-MULTIAS-V3.unl'
 check(path)
