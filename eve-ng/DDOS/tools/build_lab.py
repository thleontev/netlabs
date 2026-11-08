#!/usr/bin/env python3
"""Generate EVE-NG CE .unl (only topology: configs remain in configs/)."""
import argparse
import pathlib
import uuid
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parent.parent
LAB_ID='d5ad4943-91e1-43a8-97a2-832a01c6eae1'
# node: id,x,y, Gi0/N -> bridge-id
R={
'R-T1':(1,420,260,{0:1,1:2,2:3,3:4}),
'R-T2':(2,950,260,{0:1,1:5,2:6,3:7,4:8}),
'R-CUR1':(3,240,480,{0:2,1:9}),
'R-CUR2':(4,1130,480,{0:5,1:10}),
'R-CUR-RR':(5,685,580,{0:9,1:10}),
'R-ISP1':(6,410,680,{0:3,1:11}),
'R-ISP2':(7,960,680,{0:6,1:12}),
'R-CE':(8,685,900,{0:11,1:12,2:16}),
'R-ACCESS-CLIENT':(9,80,100,{0:4,1:13}),
'R-ACCESS-BOT1':(10,1140,100,{0:7,1:14}),
'R-ACCESS-BOT2':(11,1450,100,{0:8,1:15}),
}
V={
'CLIENT':(12,80,-80,{0:13}),
'BOT1':(13,1140,-80,{0:14}),
'BOT2':(14,1450,-80,{0:15}),
'SERVER':(15,685,1090,{0:16}),
}
NETS={1:'T1-T2',2:'T1-CUR1',3:'T1-ISP1',4:'T1-ACCESS-CLIENT',5:'T2-CUR2',6:'T2-ISP2',7:'T2-ACCESS-BOT1',8:'T2-ACCESS-BOT2',9:'CUR1-CORE',10:'CUR2-CORE',11:'ISP1-CE',12:'ISP2-CE',13:'CLIENT-LAN',14:'BOT1-LAN',15:'BOT2-LAN',16:'SERVER-LAN'}

def build(router_image:str, linux_image:str|None, output:pathlib.Path):
    lab=ET.Element('lab', {'name':'BGP GRE DDoS Multi-AS Dual Transit v3', 'id':LAB_ID,'version':'2','author':'netlabs','scripttimeout':'300','lock':'0'})
    ET.SubElement(lab,'description').text='Isolated BGP GRE training: 2 transit AS, 2 uplinks, 2 POPs with iBGP/RR, 3 access AS, dual GRE, route-leak and failover experiments.'
    topology=ET.SubElement(lab,'topology')
    nodes=ET.SubElement(topology,'nodes')
    for name,(nid,x,y,interfaces) in {**R,**V}.items():
        is_r=name in R
        is_linux=bool(linux_image and name in ('SERVER','BOT2','CLIENT'))
        node_type='qemu' if is_r or is_linux else 'vpcs'
        template='vios' if is_r else ('linux' if is_linux else 'vpcs')
        opts={'id':str(nid),'name':name,'type':node_type,'template':template,
            'console':'telnet' if not is_linux else 'vnc',
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL, f'netlabs:curator:multias:v3:{name}')),
            'ethernet':str(max(4,max(interfaces)+1) if is_r else 1),
            'icon':'Router.png' if is_r else 'Desktop.png',
            'left':str(x),'top':str(y),'config':'0','delay':'0'}
        if is_r: opts.update({'image':router_image,'cpu':'1','ram':'512'})
        if is_linux: opts.update({'image':linux_image,'cpu':'1','ram':'1024'})
        n=ET.SubElement(nodes,'node',opts)
        for iid,bridge in sorted(interfaces.items()):
            ET.SubElement(n,'interface', {'id':str(iid),'name':f'Gi0/{iid}' if is_r else 'eth0','type':'ethernet','network_id':str(bridge)})
    nets=ET.SubElement(topology,'networks')
    for bid,name in sorted(NETS.items()): ET.SubElement(nets,'network', {'id':str(bid),'type':'bridge','name':name,'left':'0','top':'0','visibility':'0'})
    ET.indent(lab,space='  ')
    output.write_bytes(ET.tostring(lab,encoding='utf-8',xml_declaration=True))
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image',default='vios-adventerprisek9-m.SPA.159-3.M6',help='Exact EVE QEMU image directory for Cisco IOSv')
    p.add_argument('--linux-image',help='Optional EVE QEMU image directory linux-*. When specified, replace CLIENT, BOT2 and SERVER VPCS by Linux QEMU nodes.')
    p.add_argument('--output',type=pathlib.Path,help='Output file (default: ROOT/CURATOR-BGP-MULTIAS-V3.unl)')
    a=p.parse_args(); path=a.output or ROOT/'CURATOR-BGP-MULTIAS-V3.unl'
    print(build(a.image,a.linux_image,path))
