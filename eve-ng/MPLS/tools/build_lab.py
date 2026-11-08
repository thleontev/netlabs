#!/usr/bin/env python3
"""Reproducible EVE-NG advanced MPLS-SP lab generator (Python stdlib only)."""
import csv
import ipaddress
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom.minidom import parseString

ROOT=Path(__file__).resolve().parents[1]
IMAGE='vios-adventerprisek9-m.SPA.159-3.M6'
AS_SP=65000

DEVICES={
'PE-W1': ('PE', '10.255.0.1', 355, 380),
'PE-W2': ('PE', '10.255.0.2', 355, 760),
'PE-E1': ('PE', '10.255.0.3', 1285, 380),
'PE-E2': ('PE', '10.255.0.4', 1285, 760),
'P1': ('P', '10.255.0.11', 660, 310),
'P2': ('P', '10.255.0.12', 660, 825),
'P3': ('P', '10.255.0.13', 980, 310),
'P4': ('P', '10.255.0.14', 980, 825),
'RR1': ('RR', '10.255.0.21', 820, 100),
'RR2': ('RR', '10.255.0.22', 820, 1015),
'CE-A-W1': ('CE-A','', 85, 185),
'CE-A-W2': ('CE-A','', 85, 790),
'CE-A-E1': ('CE-A','', 1560, 185),
'CE-A-E2': ('CE-A','', 1560, 790),
'CE-B-W': ('CE-B','', 85, 480),
'CE-B-E': ('CE-B','', 1560, 480),
}
# tuple: endpoints, costs; lower metric backbone preferred; no MPLS to RR.
CORE_LINKS=[
('PE-W1','P1',10),('PE-W1','P2',30),('PE-W2','P1',30),('PE-W2','P2',10),
('P1','P2',20),('P1','P3',10),('P1','P4',35),('P2','P3',35),('P2','P4',10),('P3','P4',20),
('P3','PE-E1',10),('P4','PE-E1',30),('P3','PE-E2',30),('P4','PE-E2',10),
('RR1','P1',10),('RR2','P4',10),
]
# Customer AS and networks. CE-A-W1 is dual attached to PE-W1 / PE-W2.
CUSTOMERS={
'CE-A-W1': ('CUST_A',65110,'10.100.1.1/24'),
'CE-A-W2': ('CUST_A',65120,'10.100.2.1/24'),
'CE-A-E1': ('CUST_A',65130,'10.100.3.1/24'),
'CE-A-E2': ('CUST_A',65140,'10.100.4.1/24'),
'CE-B-W': ('CUST_B',65210,'10.100.1.1/24'),
'CE-B-E': ('CUST_B',65220,'10.100.3.1/24'),
}
VRFS={'CUST_A': 100, 'CUST_B': 200}
# PE, CE, subnet (/30). PE has .1; CE .2.
CE_LINKS=[
('PE-W1','CE-A-W1','10.11.1.0/30'),('PE-W2','CE-A-W1','10.11.2.0/30'),
('PE-W2','CE-A-W2','10.11.3.0/30'),('PE-E1','CE-A-E1','10.11.4.0/30'),
('PE-E2','CE-A-E2','10.11.5.0/30'),('PE-W1','CE-B-W','10.12.1.0/30'),
('PE-E1','CE-B-E','10.12.2.0/30'),
]

IFACES={n:[] for n in DEVICES}
LINKS=[]
for index,(a,b,cost) in enumerate(CORE_LINKS,1):
    prefix=ipaddress.ip_network(f'172.20.{index}.0/30')
    la={'kind':'core','name':f'{a}--{b}','a':a,'b':b,'prefix':str(prefix),
        'a_ip':str(prefix.network_address+1),'b_ip':str(prefix.network_address+2),'ospf_cost':cost}
    LINKS.append(la)
for a,b,cidr in CE_LINKS:
    prefix=ipaddress.ip_network(cidr)
    LINKS.append({'kind':'ce','name':f'{a}--{b}','a':a,'b':b,'prefix':cidr,
        'a_ip':str(prefix.network_address+1),'b_ip':str(prefix.network_address+2),
        'ospf_cost':None,'vrf':CUSTOMERS[b][0]})

# Deterministic natural NIC assignment. Each NIC belongs to precisely one link.
for seq,l in enumerate(LINKS,1):
    l['network_id']=seq
    for end,key in (('a','a_ip'),('b','b_ip')):
        n=l[end]
        i=len(IFACES[n]); assert i<8,(n,i)
        l[end+'_if']=f'GigabitEthernet0/{i}'
        l[end+'_if_id']=i
        IFACES[n].append({'link':l,'ip':l[key],'iface':l[end+'_if'],'kind':l['kind'], 'side':end})

# CE-W1: 1st attachment goes to PE-W1, second to PE-W2 due insertion order.

def netmask(prefix): return str(ipaddress.ip_network(prefix).netmask)

def rconfig(node,stage):
    role,loop,_,_=DEVICES[node]
    ls=['enable','configure terminal',f'hostname {node}','no ip domain-lookup','ip cef','no logging console','!']
    if role not in ('CE-A','CE-B'):
        ls += ['interface Loopback0',f' ip address {loop} 255.255.255.255',' no shutdown','!']
    else:
        vrf,asn,lan=CUSTOMERS[node]
        addr=ipaddress.ip_interface(lan)
        ls += ['interface Loopback0',f' ip address {addr.ip} {addr.network.netmask}',' no shutdown','!']
    if role == 'PE' and stage==2:
        for vrf,rt in VRFS.items():
            # Separate RD per PE per VRF (not identical across PEs).
            peid=int(loop.rsplit('.',1)[-1]); rd=rt*10+peid
            ls += [f'ip vrf {vrf}',f' rd {AS_SP}:{rd}',f' route-target export {AS_SP}:{rt}',
                f' route-target import {AS_SP}:{rt}','!']
    for ni in IFACES[node]:
        l=ni['link']; intf=ni['iface']; ip=ni['ip']
        ls += [f'interface {intf}',f' description TO_{l["b" if ni["side"]=="a" else "a"]}']
        if role == 'PE' and stage==2 and l['kind']=='ce': ls += [f' ip vrf forwarding {l["vrf"]}']
        ls += [f' ip address {ip} {netmask(l["prefix"])}',' no shutdown']
        if l['kind']=='core':
            ls += [' ip ospf 100 area 0',' ip ospf network point-to-point', f' ip ospf cost {l["ospf_cost"]}']
            if stage>=1 and role!='RR': ls += [' mpls ip']
        ls += ['!']
    if role not in ('CE-A','CE-B'):
        ls += ['interface Loopback0',' ip ospf 100 area 0','!']
        ls += ['router ospf 100',f' router-id {loop}',' passive-interface Loopback0','!']
        if stage>=1 and role!='RR': ls += ['mpls label protocol ldp','mpls ldp router-id Loopback0 force','!']
    if stage==2 and role in ('PE','RR'):
        ls += [f'router bgp {AS_SP}',f' bgp router-id {loop}', ' bgp log-neighbor-changes',
               ' no bgp default ipv4-unicast']
        if role=='PE':
            for rr in ['RR1','RR2']:
                rrlo=DEVICES[rr][1]
                ls += [f' neighbor {rrlo} remote-as {AS_SP}',f' neighbor {rrlo} update-source Loopback0']
            ls += [' address-family vpnv4']
            for rr in ['RR1','RR2']:
                rrlo=DEVICES[rr][1]
                ls += [f'  neighbor {rrlo} activate',f'  neighbor {rrlo} send-community extended']
            ls += [' exit-address-family']
            for vrf in VRFS:
                ceconnections=[l for l in LINKS if l['kind']=='ce' and l['a']==node and l['vrf']==vrf]
                if not ceconnections: continue
                ls += [f' address-family ipv4 vrf {vrf}']
                for l in ceconnections:
                    ce_as=CUSTOMERS[l['b']][1]; ip=l['b_ip']
                    ls += [f'  neighbor {ip} remote-as {ce_as}',f'  neighbor {ip} activate']
                    if node=='PE-W1' and l['b']=='CE-A-W1':
                        ls += [f'  neighbor {ip} route-map PREFER-W1 in']
                ls += [' exit-address-family']
            ls += ['!']
            if node=='PE-W1':
                ls += ['route-map PREFER-W1 permit 10',' set local-preference 200','!']
        else:
            for pe in ['PE-W1','PE-W2','PE-E1','PE-E2']:
                pe_lo=DEVICES[pe][1]
                ls += [f' neighbor {pe_lo} remote-as {AS_SP}',f' neighbor {pe_lo} update-source Loopback0']
            ls += [' address-family vpnv4']
            for pe in ['PE-W1','PE-W2','PE-E1','PE-E2']:
                pe_lo=DEVICES[pe][1]
                ls += [f'  neighbor {pe_lo} activate',f'  neighbor {pe_lo} send-community extended',
                       f'  neighbor {pe_lo} route-reflector-client']
            ls += [' exit-address-family','!']
    if stage==2 and role in ('CE-A','CE-B'):
        vrf,asn,lan=CUSTOMERS[node]
        prefix=ipaddress.ip_interface(lan).network
        ls += [f'router bgp {asn}', ' bgp log-neighbor-changes', f' network {prefix.network_address} mask {prefix.netmask}']
        adj=[l for l in LINKS if l['kind']=='ce' and l['b']==node]
        for l in adj:
            ip=l['a_ip']
            ls += [f' neighbor {ip} remote-as {AS_SP}']
            if node=='CE-A-W1' and l['a']=='PE-W1': ls += [f' neighbor {ip} weight 500']
        ls += ['!']
    ls += ['end']
    return '\n'.join(ls)+'\n'


def make_unl():
    lab=ET.Element('lab',{'name':'MPLS-SP-Advanced','id':'1d55d457-c2e1-47ab-a2ea-105aff505001','version':'1','scripttimeout':'300','countdown':'0','lock':'0','sat':'-1',
                          'description':'16 nodes: OSPF/LDP MPLS core, redundant VPNv4 route-reflectors, 2 VRFs, multi-homed CE, troubleshooting','body':''})
    topo=ET.SubElement(lab,'topology')
    nodes=ET.SubElement(topo,'nodes')
    for n,(role,loop,x,y) in DEVICES.items():
        idx=list(DEVICES).index(n)+1
        attrs={'id':str(idx),'name':n,'type':'qemu','template':'vios','image':IMAGE,'console':'telnet',
               'cpu':'1','cpulimit':'0','ram': '512' if role.startswith('CE-') else ('768' if role=='RR' else '1024'),
               'ethernet':'8' if role in ('P','PE') else '4',
               'uuid':f'890a0010-0001-4000-8000-{idx:012d}',
               'firstmac':f'50:00:00:{idx:02x}:00:00','sat':'-1','left':str(x),'top':str(y),'icon':'Router.png','config':'0','delay':'0','shutdowntime':'5'}
        el=ET.SubElement(nodes,'node',attrs)
        for nic in IFACES[n]:
            ET.SubElement(el,'interface',{'id':str(nic['link'][nic['side']+'_if_id']),
                'name':nic['iface'],'type':'ethernet','network_id':str(nic['link']['network_id'])})
    nets=ET.SubElement(topo,'networks')
    for l in LINKS:
        a,b=DEVICES[l['a']],DEVICES[l['b']]
        ET.SubElement(nets,'network',{'id':str(l['network_id']),'type':'bridge','name':l['name'],
            'left':str(round((a[2]+b[2])/2)),'top':str(round((a[3]+b[3])/2)),
            'L2':'0','expanded':'0','visibility':'0'})
    ET.SubElement(ET.SubElement(lab,'objects'),'configs')
    rough=ET.tostring(lab,encoding='utf-8')
    out=parseString(rough).toprettyxml(indent='  ',encoding='UTF-8').decode('utf-8')
    (ROOT/'MPLS-SP-Advanced.unl').write_text(out,encoding='utf-8')


def make():
    make_unl()
    for stage,folder in enumerate(('00-underlay','01-ldp','02-l3vpn')):
        dest=ROOT/'configs'/folder
        dest.mkdir(exist_ok=True,parents=True)
        for n in DEVICES:
            (dest/f'{n}.cfg').write_text(rconfig(n,stage),encoding='utf-8')
    (ROOT/'docs').mkdir(exist_ok=True)
    fields=['link','network_id','type','node_a','interface_a','ip_a','node_b','interface_b','ip_b','subnet','ospf_cost','vrf']
    with (ROOT/'docs'/'LINKS.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for l in LINKS:
            w.writerow({'link':l['name'],'network_id':l['network_id'],'type':l['kind'],'node_a':l['a'],
                'interface_a':l['a_if'],'ip_a':l['a_ip'],'node_b':l['b'],'interface_b':l['b_if'],'ip_b':l['b_ip'],
                'subnet':l['prefix'],'ospf_cost':l['ospf_cost'] or '', 'vrf':l.get('vrf','')})
    data={'image':IMAGE,'devices':{n:{'role':v[0],'loopback':v[1],'position':[v[2],v[3]]} for n,v in DEVICES.items()},
          'links':LINKS,'customers':{k:{'vrf':v[0],'asn':v[1],'lan':v[2]} for k,v in CUSTOMERS.items()}}
    (ROOT/'docs'/'topology.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Generated EVE-NG topology:',len(DEVICES),'devices',len(LINKS),'links',len(DEVICES)*3,'configurations')
if __name__=='__main__':make()
