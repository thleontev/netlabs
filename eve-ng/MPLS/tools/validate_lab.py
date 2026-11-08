#!/usr/bin/env python3
"""Static regression checks for EVE-NG topology and corresponding IOSv CLI files.
Does NOT emulate Cisco IOS or prove operational traffic forwarding.
"""
import collections
import heapq
import ipaddress
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]

model=json.loads((ROOT/'docs'/'topology.json').read_text(encoding='utf-8'))
D=model['devices']; L=model['links']
errors=[]
def check(ok,msg):
    if not ok:errors.append(msg)

try:
    tree=ET.parse(ROOT/'MPLS-SP-Advanced.unl')
except Exception as exc:
    raise SystemExit(f'FAIL: invalid unl: {exc}')
root=tree.getroot();top=root.find('topology')
xml_nodes={n.get('name'):n for n in top.find('nodes').findall('node')}
xml_nets={int(n.get('id')):n for n in top.find('networks').findall('network')}
check(len(xml_nodes)==16,'expected 16 nodes')
check(len(xml_nets)==23,'expected 23 bridge networks')
check(set(xml_nodes)==set(D),'XML and model device names mismatch')
check(len({n.get('uuid') for n in xml_nodes.values()})==len(xml_nodes),'duplicate node UUID')

ref=collections.defaultdict(list)
for name,node in xml_nodes.items():
    ifaces=node.findall('interface')
    ids=[int(i.get('id')) for i in ifaces]
    check(len(ids)==len(set(ids)),f'{name} duplicate interface IDs')
    check(all(i< int(node.get('ethernet')) for i in ids),f'{name} exceeds EVE interface count')
    for iface in ifaces: ref[int(iface.get('network_id'))].append((name,iface.get('name')))
for id,net in xml_nets.items():check(len(ref[id])==2,f'{id} must have exactly two interfaces (got {len(ref[id])})')
check(set(ref)==set(xml_nets),'missing / unused network IDs')

all_ip=[]
for l in L:
    rid=l['network_id']; net=ipaddress.ip_network(l['prefix'])
    ends={(l['a'],l['a_if']),(l['b'],l['b_if'])}
    check(set(ref[rid])==ends,f'network {rid} interface mismatch')
    check(xml_nets[rid].get('name')==l['name'],f'network {rid} name mismatch')
    for key in ('a_ip','b_ip'):
        addr=ipaddress.ip_address(l[key])
        check(addr in net,f'{l["name"]}: address outside prefix')
        all_ip.append(str(addr))
check(len(all_ip)==len(set(all_ip)),'duplicate physical IPv4 addresses')

rds=[]
for name,device in D.items():
    role=device['role']
    for stage,folder in enumerate(('00-underlay','01-ldp','02-l3vpn')):
        path=ROOT/'configs'/folder/f'{name}.cfg'
        check(path.exists(),f'missing {path}')
        if not path.exists():continue
        cfg=path.read_text(encoding='utf-8')
        check(f'hostname {name}' in cfg,f'{folder}/{name} hostname')
        check('end' in cfg.splitlines()[-1],f'{folder}/{name} no config terminator')
        if device['loopback']:
            check(device['loopback'] in cfg,f'{folder}/{name} loopback missing')
        if stage<1:
            check('mpls ip' not in cfg and 'router bgp ' not in cfg,f'{folder}/{name} unexpectedly includes MPLS/BGP')
        if stage==1:
            check('router bgp ' not in cfg,f'{folder}/{name} unexpectedly includes BGP')
        if role=='RR':
            check('mpls ip' not in cfg,f'{folder}/{name} MPLS incorrectly enabled on RR')
        if stage==2:
            if role=='PE':
                check('address-family vpnv4' in cfg,f'{name} missing VPNv4')
                rds += re.findall(r'^ rd (\d+:\d+)$',cfg,re.M)
                for neighbor in ('10.255.0.21','10.255.0.22'):
                    check(f'neighbor {neighbor} activate' in cfg,f'{name} missing RR {neighbor}')
            if role=='RR':
                for neighbor in ('10.255.0.1','10.255.0.2','10.255.0.3','10.255.0.4'):
                    check(f'neighbor {neighbor} route-reflector-client' in cfg,f'{name} missing client {neighbor}')
            if role=='P':check('router bgp ' not in cfg,f'{name} should not carry BGP')
    # Per-link consistency across complete cfg
    cfg=(ROOT/'configs'/'02-l3vpn'/f'{name}.cfg').read_text(encoding='utf-8')
    for l in L:
        if name in (l['a'],l['b']):
            side='a' if name==l['a'] else 'b'
            check(f'interface {l[side+"_if"]}' in cfg,f'{name} interface absent on {l["name"]}')
            check(f'ip address {l[side+"_ip"]} {ipaddress.ip_network(l["prefix"]).netmask}' in cfg,
                  f'{name} incorrect IP on {l["name"]}')
            if l['kind']=='core' and role!='RR':
                check(cfg.count(' mpls ip')==sum(1 for ll in L if ll['kind']=='core' and name in (ll['a'],ll['b'])),
                      f'{name}: unexpected MPLS interface count')
            if l['kind']=='ce':
                if role=='PE':check(f'ip vrf forwarding {l["vrf"]}' in cfg,f'{name} missing VRF')
                if role.startswith('CE-'):
                    check(f'neighbor {l["a_ip"]} remote-as 65000' in cfg,f'{name} missing eBGP peer')
check(len(rds)==8,f'expected 8 unique PE/VRF RD entries, got {len(rds)}')
check(len(set(rds))==len(rds),'duplicate RD')

# Graph shortest path analysis (stdlib Dijkstra) and failover assertions.
def path(src,dst,blocked=None):
    blocked=blocked or set();g=collections.defaultdict(list)
    for l in L:
        if l['kind']!='core':continue
        edge=frozenset((l['a'],l['b']))
        if edge in blocked:continue
        g[l['a']].append((l['b'],l['ospf_cost']))
        g[l['b']].append((l['a'],l['ospf_cost']))
    todo=[(0,src,(src,))];seen={}
    while todo:
        cost,n,p=heapq.heappop(todo)
        if n in seen: continue
        seen[n]=cost
        if n==dst:return cost,p
        for nxt,w in g[n]:
            if nxt not in seen:heapq.heappush(todo,(cost+w,nxt,p+(nxt,)))
    return None,()

c,p=path('PE-W1','PE-E1')
check(c==30 and p==('PE-W1','P1','P3','PE-E1'),f'primary west→east unexpected: {c} {p}')
for cut in (frozenset(('P1','P3')),frozenset(('P2','P4'))):
    alt,route=path('PE-W1','PE-E1',{cut})
    check(alt is not None and alt>=30,f'failure {cut} has no alternate path')
for rr in ('RR1','RR2'):
    check(path('PE-W1',rr)[0] is not None,f'{rr} unreachable')

# Conform route export/import isolation
pe=[k for k,v in D.items() if v['role']=='PE']
for node in pe:
    cfg=(ROOT/'configs'/'02-l3vpn'/f'{node}.cfg').read_text(encoding='utf-8')
    for vrf,rt in (('CUST_A',100),('CUST_B',200)):
        block=cfg.split(f'ip vrf {vrf}\n',1)[1].split('\n!',1)[0] if f'ip vrf {vrf}\n' in cfg else ''
        check(f'route-target import 65000:{rt}' in block,f'{node} {vrf} RT')
        check(f'route-target import 65000:{200 if rt==100 else 100}' not in block,
              f'{node} customer RT leaked into {vrf}')

if errors:
    for e in errors:print('FAIL:',e)
    sys.exit(1)
print(f'PASS: {len(xml_nodes)} nodes, {len(xml_nets)} links, {len(D)*3} CLI configs, {len(rds)} distinct RD')
print(f'PASS: primary PE-W1→PE-E1 cost={c}, path={" → ".join(p)}')
print('PASS: backup core path remains after either inter-P backbone link failure')
print('NOTE: static checks only; protocol convergence and IOSv syntax require a live EVE-NG run')
