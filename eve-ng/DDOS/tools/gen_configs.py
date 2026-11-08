#!/usr/bin/env python3
"""Build reproducible IOSv configurations for the Multi-AS EVE-NG lab."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'configs'; OUT.mkdir(exist_ok=True)
A='203.0.113.0/24'
PREFIX={
 'PROTECTED':['203.0.113.0/24'],
 'POP-ENDPOINTS':['198.18.0.21/32','198.18.0.22/32'],
 'UNDERLAY-WANS':['198.18.11.0/30','198.18.12.0/30'],
 'ACCESS-CLIENT':['198.18.100.0/24'],
 'ACCESS-BOT1':['198.18.101.0/24'],
 'ACCESS-BOT2':['198.18.102.0/24'],
 'ONLY-DEFAULT':['0.0.0.0/0'],
 'DENY-ALL':[],
 'TRANSIT-SAFE':['203.0.113.0/24','198.18.0.21/32','198.18.0.22/32','198.18.11.0/30','198.18.12.0/30','198.18.100.0/24','198.18.101.0/24','198.18.102.0/24'],
}
def intf(name,ip,mask,desc,extra=''):
 return f'interface {name}\n description {desc}\n ip address {ip} {mask}\n'+(extra+'\n' if extra else '')+' no shutdown\n!\n'
def plist(name,values):
 return '\n'.join(f'ip prefix-list {name} seq {i*5} permit {v}' for i,v in enumerate(values,1))+ ('\n' if values else f'ip prefix-list {name} seq 5 deny 0.0.0.0/0 le 32\n')
def pl(*keys): return ''.join(plist(k,PREFIX[k]) for k in keys)+'!\n'
def bgp_neighbors(entries):
 # entries: ip, as, inPrefix, outPrefix, extra
 s=''
 for peer,asn,pin,pout,extra in entries:
  s+=f' neighbor {peer} remote-as {asn}\n'
  if pin: s+=f' neighbor {peer} prefix-list {pin} in\n'
  if pout: s+=f' neighbor {peer} prefix-list {pout} out\n'
  for val in extra: s+=f' neighbor {peer} {val}\n'
 return s
def save(name,content):
 (OUT/f'{name}.cfg').write_text(content.strip()+ '\n',encoding='utf-8')

def transit(name,asn,links,peer_rules,default_peers):
 cfg=f'hostname {name}\nno ip domain-lookup\n!\n'
 for ifn,ip,description in links:
  cfg+=intf(ifn,ip,'255.255.255.252',description)
 cfg+=pl('PROTECTED','POP-ENDPOINTS','UNDERLAY-WANS','ACCESS-CLIENT','ACCESS-BOT1','ACCESS-BOT2','TRANSIT-SAFE')
 cfg+=f'router bgp {asn}\n bgp log-neighbor-changes\n'
 for addr,remote_as,inp,outp,extras in peer_rules:
  cfg+=bgp_neighbors([(addr,remote_as,inp,outp,extras)])
 for peer in default_peers:
  cfg+=f' neighbor {peer} default-originate\n'
 cfg+='!\nend\n'
 save(name,cfg)

# AS65000 and AS65001 peer publicly and propagate a strictly filtered set of lab prefixes.
transit('R-T1',65000,[
 ('GigabitEthernet0/0','10.1.0.1','TRANSIT_TO_T2_AS65001'),
 ('GigabitEthernet0/1','10.1.0.5','TO_CUR1_AS65020'),
 ('GigabitEthernet0/2','10.1.0.9','TO_ISP1_AS65011'),
 ('GigabitEthernet0/3','10.1.0.13','TO_CLIENT_ACCESS_AS65031')],
 [('10.1.0.2',65001,'TRANSIT-SAFE','TRANSIT-SAFE',[]),
  ('10.1.0.6',65020,'CUR1-IN','UNDERLAY-WANS',[]),
  ('10.1.0.10',65011,'ISP1-IN','POP-ENDPOINTS',[]),
  ('10.1.0.14',65031,'ACCESS-CLIENT','PROTECTED',[])],
 ['10.1.0.14'])
transit('R-T2',65001,[
 ('GigabitEthernet0/0','10.1.0.2','TRANSIT_TO_T1_AS65000'),
 ('GigabitEthernet0/1','10.1.0.17','TO_CUR2_AS65020'),
 ('GigabitEthernet0/2','10.1.0.21','TO_ISP2_AS65012'),
 ('GigabitEthernet0/3','10.1.0.25','TO_BOT1_AS65041'),
 ('GigabitEthernet0/4','10.1.0.29','TO_BOT2_AS65042')],
 [('10.1.0.1',65000,'TRANSIT-SAFE','TRANSIT-SAFE',[]),
  ('10.1.0.18',65020,'CUR2-IN','UNDERLAY-WANS',[]),
  ('10.1.0.22',65012,'ISP2-IN','POP-ENDPOINTS',[]),
  ('10.1.0.26',65041,'ACCESS-BOT1','PROTECTED',[]),
  ('10.1.0.30',65042,'ACCESS-BOT2','PROTECTED',[])],
 ['10.1.0.26','10.1.0.30'])
# Transit neighbors have explicit allowlists, including exception paths for testing a leak.

for n,asn,peer,lan,hostip,desc in [
 ('R-ACCESS-CLIENT',65031,'10.1.0.13','198.18.100.0','198.18.100.1','CLIENT'),
 ('R-ACCESS-BOT1',65041,'10.1.0.25','198.18.101.0','198.18.101.1','BOT1'),
 ('R-ACCESS-BOT2',65042,'10.1.0.29','198.18.102.0','198.18.102.1','BOT2'),
]:
 local={'R-ACCESS-CLIENT':'10.1.0.14','R-ACCESS-BOT1':'10.1.0.26','R-ACCESS-BOT2':'10.1.0.30'}[n]
 lanpref={'R-ACCESS-CLIENT':'ACCESS-CLIENT','R-ACCESS-BOT1':'ACCESS-BOT1','R-ACCESS-BOT2':'ACCESS-BOT2'}[n]
 cfg=f'hostname {n}\nno ip domain-lookup\n!\n'
 cfg+=intf('GigabitEthernet0/0',local,'255.255.255.252','UPSTREAM_TO_TRANSIT')
 cfg+=intf('GigabitEthernet0/1',hostip,'255.255.255.0','LAN_'+desc)
 cfg+=pl(lanpref,'PROTECTED','ONLY-DEFAULT')
 cfg+=f'router bgp {asn}\n bgp log-neighbor-changes\n'
 cfg+=f' network {lan} mask 255.255.255.0\n'
 cfg+=bgp_neighbors([(peer,65000 if n=='R-ACCESS-CLIENT' else 65001,'PROTECTED',lanpref,[])])
 cfg+='!\nend'
 save(n,cfg)

for num in (1,2):
 name=f'R-ISP{num}'
 transit_as=65000 if num==1 else 65001
 upstream='10.1.0.9' if num==1 else '10.1.0.21'
 local='10.1.0.10' if num==1 else '10.1.0.22'
 wan=f'198.18.{10+num}.0'
 gw=f'198.18.{10+num}.1'
 ce=f'198.18.{10+num}.2'
 cfg=f'hostname {name}\nno ip domain-lookup\n!\n'
 cfg+=intf('GigabitEthernet0/0',local,'255.255.255.252','UPSTREAM_TRANSIT')
 cfg+=intf('GigabitEthernet0/1',gw,'255.255.255.252','CE_UNDERLAY')
 cfg+=f'ip route 0.0.0.0 0.0.0.0 {upstream}\n!\n'
 cfg+=pl('POP-ENDPOINTS','ONLY-DEFAULT','DENY-ALL')
 cfg+=plist(f'ISP{num}-EXPORT',[f'{wan}/30'])
 cfg+=f'router bgp {65010+num}\n bgp log-neighbor-changes\n network {wan} mask 255.255.255.252\n'
 cfg+=bgp_neighbors([(upstream,transit_as,'POP-ENDPOINTS',f'ISP{num}-EXPORT',[]),(ce,65010,'DENY-ALL','ONLY-DEFAULT',['default-originate'])])
 cfg+='!\nend'
 save(name,cfg)

for num in (1,2):
 name=f'R-CUR{num}'
 uplink='10.1.0.5' if num==1 else '10.1.0.17'
 outer='10.1.0.6' if num==1 else '10.1.0.18'
 transit_as=65000 if num==1 else 65001
 core_addr='10.2.0.1' if num==1 else '10.2.0.5'
 core_peer='10.2.0.2' if num==1 else '10.2.0.6'
 public=f'198.18.0.{20+num}'
 remote=f'198.18.{10+num}.2'
 tunnel=f'172.31.{num}.1'; ce_tunnel=f'172.31.{num}.2'
 cfg=f'hostname {name}\nno ip domain-lookup\n!\n'
 cfg+=intf('GigabitEthernet0/0',outer,'255.255.255.252','TRANSIT_INBOUND_AND_OUTBOUND', ' ip access-group SCRUB-POLICY in')
 cfg+=intf('GigabitEthernet0/1',core_addr,'255.255.255.252','PRIVATE_BACKBONE_TO_ROUTE_REFLECTOR')
 cfg+=intf('Loopback0',public,'255.255.255.255','GRE_ENDPOINT_AND_IBGP_PEERING')
 cfg+=f'''interface Tunnel{num}
 description SCRUBBED_GRE_TO_CE_{num}
 ip address {tunnel} 255.255.255.252
 ip mtu 1476
 ip tcp adjust-mss 1436
 tunnel source Loopback0
 tunnel destination {remote}
 tunnel mode gre ip
 no shutdown
!
'''
 cfg+=f'ip route 0.0.0.0 0.0.0.0 {uplink}\n!\n'
 cfg+='''ip access-list extended SCRUB-POLICY
 remark TRAINING ACL ONLY - not production anti-DDoS
 deny icmp host 198.18.101.10 host 203.0.113.10 echo
 deny icmp host 198.18.102.10 host 203.0.113.10 echo
 deny tcp host 198.18.101.10 host 203.0.113.10 eq 80
 deny tcp host 198.18.102.10 host 203.0.113.10 eq 80
 permit ip any any
!
'''
 cfg+=f'''router ospf 20
 router-id {public}
 passive-interface default
 no passive-interface GigabitEthernet0/1
 network {core_addr} 0.0.0.0 area 0
 network {public} 0.0.0.0 area 0
!
'''
 cfg+=pl('PROTECTED','ONLY-DEFAULT','UNDERLAY-WANS')
 cfg+=plist('POP-LOCAL', [public+'/32','203.0.113.0/24'])
 cfg+=f'''router bgp 65020
 bgp log-neighbor-changes
 bgp router-id {public}
 network {public} mask 255.255.255.255
'''
 cfg+=bgp_neighbors([(uplink,transit_as,'UNDERLAY-WANS','POP-LOCAL',[]), (ce_tunnel,65010,'PROTECTED','ONLY-DEFAULT',['default-originate','timers 10 30']), ('198.19.0.200',65020,'PROTECTED','PROTECTED',['update-source Loopback0','next-hop-self'])])
 cfg+='!\nend'
 save(name,cfg)

cfg='''hostname R-CUR-RR
no ip domain-lookup
!
'''
cfg+=intf('GigabitEthernet0/0','10.2.0.2','255.255.255.252','BACKBONE_TO_POP1')
cfg+=intf('GigabitEthernet0/1','10.2.0.6','255.255.255.252','BACKBONE_TO_POP2')
cfg+=intf('Loopback0','198.19.0.200','255.255.255.255','RR_LOOPBACK')
cfg+='''router ospf 20
 router-id 198.19.0.200
 passive-interface default
 no passive-interface GigabitEthernet0/0
 no passive-interface GigabitEthernet0/1
 network 10.2.0.2 0.0.0.0 area 0
 network 10.2.0.6 0.0.0.0 area 0
 network 198.19.0.200 0.0.0.0 area 0
!
'''
cfg+=pl('PROTECTED')
cfg+='''router bgp 65020
 bgp log-neighbor-changes
 bgp router-id 198.19.0.200
'''
for addr in ['198.18.0.21','198.18.0.22']:
 cfg+=bgp_neighbors([(addr,65020,'PROTECTED','PROTECTED',['update-source Loopback0','route-reflector-client'])])
cfg+='!\nend'
save('R-CUR-RR',cfg)

cfg='''hostname R-CE
no ip domain-lookup
!
'''
cfg+=intf('GigabitEthernet0/0','198.18.11.2','255.255.255.252','ISP1_UNDERLAY')
cfg+=intf('GigabitEthernet0/1','198.18.12.2','255.255.255.252','ISP2_UNDERLAY')
cfg+=intf('GigabitEthernet0/2','203.0.113.1','255.255.255.0','PROTECTED_SERVER_LAN')
for num in (1,2):
 cfg+=f'''interface Tunnel{num}
 description OVER_ISP{num}_TO_CUR{num}
 ip address 172.31.{num}.2 255.255.255.252
 ip mtu 1476
 ip tcp adjust-mss 1436
 tunnel source GigabitEthernet0/{num-1}
 tunnel destination 198.18.0.{20+num}
 tunnel mode gre ip
 no shutdown
!
'''
cfg+='''! Pin GRE underlay to physically separate ISPs (prevent recursive routing).
ip route 198.18.0.21 255.255.255.255 198.18.11.1
ip route 198.18.0.22 255.255.255.255 198.18.12.1
!
'''
cfg+=pl('PROTECTED','ONLY-DEFAULT','DENY-ALL')
cfg+='''route-map PREF-CUR1 permit 10
 set local-preference 250
route-map PREF-CUR2 permit 10
 set local-preference 200
route-map PREF-ISP1 permit 10
 set local-preference 90
route-map PREF-ISP2 permit 10
 set local-preference 80
!
router bgp 65010
 bgp log-neighbor-changes
 network 203.0.113.0 mask 255.255.255.0
'''
for ip,asn,route in [('198.18.11.1',65011,'PREF-ISP1'),('198.18.12.1',65012,'PREF-ISP2'),('172.31.1.1',65020,'PREF-CUR1'),('172.31.2.1',65020,'PREF-CUR2')]:
 incoming='ONLY-DEFAULT'; outgoing='PROTECTED' if asn==65020 else 'DENY-ALL'
 cfg+=bgp_neighbors([(ip,asn,incoming,outgoing,[f'route-map {route} in'] + (['timers 10 30'] if asn==65020 else []))])
cfg+='!\nend';save('R-CE',cfg)

# Replace default secure lists with interface-specific constrained intake on transit routers.
for name in ('R-T1','R-T2'):
 path=OUT/f'{name}.cfg'; s=path.read_text();
 if name=='R-T1':
  s=s.replace('router bgp ', plist('CUR1-IN',['198.18.0.21/32','203.0.113.0/24'])+plist('ISP1-IN',['198.18.11.0/30'])+'!\nrouter bgp ',1) if 'ip prefix-list CUR1-IN' not in s else s
 else:
  s=s.replace('router bgp ', plist('CUR2-IN',['198.18.0.22/32','203.0.113.0/24'])+plist('ISP2-IN',['198.18.12.0/30'])+'!\nrouter bgp ',1) if 'ip prefix-list CUR2-IN' not in s else s
 if name=='R-T1':
  s=s.replace('router bgp 65000', 'route-map FROM-ISP1 permit 10\n match ip address prefix-list PROTECTED\n set local-preference 350\nroute-map FROM-ISP1 permit 20\n set local-preference 100\n!\nrouter bgp 65000',1)
  s=s.replace(' neighbor 10.1.0.10 prefix-list ISP1-IN in', ' neighbor 10.1.0.10 prefix-list ISP1-IN in\n neighbor 10.1.0.10 route-map FROM-ISP1 in',1)
 path.write_text(s)
print('Generated',len(list(OUT.glob('*.cfg'))),'router configs.')
