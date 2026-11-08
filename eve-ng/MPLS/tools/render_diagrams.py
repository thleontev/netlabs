#!/usr/bin/env python3
"""Render editable SVG network diagram and pixel-perfect PNG exports."""
import json
from pathlib import Path
import svgwrite
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/'docs'/'topology.json').read_text(encoding='utf-8'))
nodes=source['devices'];links=source['links']

W,H=1820,1255
Sx,Sy=40,70
POS={n:(v['position'][0]+Sx,v['position'][1]+Sy) for n,v in nodes.items()}
colors={'bg':'#F5F8FD','ink':'#132641','muted':'#51647D','line':'#8292A8',
'core':'#1765C1','backup':'#1A9EAE','rr':'#8064D6','ca':'#16A07D','cb':'#D08A31',
'providerbg':'#E8F2FC','white':'#FFFFFF'}
FONT='DejaVu Sans, Arial, sans-serif'

def label(d,text,x,y,fs=18,color='ink',weight=400,anchor='start'):
    return d.add(d.text(text, insert=(x,y),font_family=FONT,font_size=fs,font_weight=weight,
                        text_anchor=anchor,fill=colors.get(color,color)))

def bubble(d, text,x,y, stroke='#CAD6E6',fs=14):
    width=18+len(text)*fs*.58
    d.add(d.rect(insert=(x-width/2,y-14),size=(width,28),rx=12,fill=colors['white'],stroke=stroke,stroke_width=1))
    label(d,text,x,y+5,fs,'ink',600,'middle')

def node_box(d,name):
    role=nodes[name]['role']
    x,y=POS[name]
    if role=='PE':
        col=colors['core'];fill='#E2F0FF';sub='PROVIDER EDGE'
    elif role=='P':
        col='#366A9E';fill='#EAF2FF';sub='CORE LSR'
    elif role=='RR':
        col=colors['rr'];fill='#F1EBFF';sub='VPNv4 RR'
    else:
        col=colors['ca'] if role=='CE-A' else colors['cb']
        fill='#E6FAF1' if role=='CE-A' else '#FFF5E4'
        sub='CUST_A' if role=='CE-A' else 'CUST_B'
    ww=135 if role in ('PE','CE-A','CE-B') else 107
    hh=70
    group=d.g()
    group.add(d.rect(insert=(x-ww/2,y-hh/2),size=(ww,hh),rx=15,fill=fill,stroke=col,stroke_width=2.6))
    # small router glyph as simple concentric circles
    group.add(d.circle(center=(x-ww/2+17,y-18),r=6,fill=col,fill_opacity=.10,stroke=col,stroke_width=1.2))
    group.add(d.path(d=f'M{x-ww/2+14},{y-18} h6 M{x-ww/2+17},{y-21} v6',stroke=col,stroke_width=1))
    group.add(d.text(name,insert=(x,y+0),font_family=FONT,font_size=17,font_weight='bold',fill=colors['ink'],text_anchor='middle'))
    group.add(d.text(sub,insert=(x,y+22),font_family=FONT,font_size=10.5,font_weight=600,fill=col,text_anchor='middle'))
    if nodes[name]['loopback']:
        group.add(d.text(nodes[name]['loopback']+'/32',insert=(x,y-14),font_family=FONT,
                         font_size=11.5,font_weight=500,fill=colors['muted'],text_anchor='middle'))
    d.add(group)


def render_overview():
    d=svgwrite.Drawing(str(ROOT/'docs'/'topology.svg'),size=(W,H),viewBox=f'0 0 {W} {H}',profile='full')
    d.add(d.rect(insert=(0,0),size=(W,H),fill=colors['bg']))
    d.add(d.rect(insert=(244,135),size=(1144,1005),rx=25,fill=colors['providerbg'],stroke='#A9C6E9',stroke_width=2))
    d.add(d.rect(insert=(12,150),size=(206,990),rx=22,fill='#F9FBFD',stroke='#B9C8D9',stroke_width=1.6,stroke_dasharray='6,5'))
    d.add(d.rect(insert=(1408,150),size=(385,990),rx=22,fill='#F9FBFD',stroke='#B9C8D9',stroke_width=1.6,stroke_dasharray='6,5'))
    label(d,'MPLS SERVICE PROVIDER — ADVANCED',45,55,31,'ink',700)
    label(d,'EVE-NG CE  •  16 routers  •  OSPF area 0  •  MPLS LDP  •  MP-BGP VPNv4  •  dual-homed CE',45,90,17,'muted')
    label(d,'PROVIDER CORE  /  AS 65000',275,174,21,'core',700)
    label(d,'Route Reflectors are IP control-plane nodes (no MPLS on RR links)',275,201,13,'muted')
    label(d,'CUSTOMER WEST',37,182,14,'muted',600)
    label(d,'CUSTOMER EAST',1430,182,14,'muted',600)
    label(d,'Core OSPF metrics are included in the detailed link table',275,230,13,'muted')

    primary={frozenset(('PE-W1','P1')),frozenset(('P1','P3')),frozenset(('P3','PE-E1'))}
    alternate={frozenset(('PE-W2','P2')),frozenset(('P2','P4')),frozenset(('P4','PE-E2'))}
    for l in links:
        a,b=l['a'],l['b'];x1,y1=POS[a];x2,y2=POS[b]
        k=frozenset((a,b))
        if l['kind']=='ce':
            col=colors['ca'] if l.get('vrf')=='CUST_A' else colors['cb'];sw=3.4;dash=None
        elif a.startswith('RR') or b.startswith('RR'):
            col=colors['rr'];sw=2.5;dash='7 6'
        elif k in primary:
            col=colors['core'];sw=4.6;dash=None
        elif k in alternate:
            col=colors['backup'];sw=4;dash=None
        else:
            col='#8396AA';sw=2.3;dash=None
        line=d.line((x1,y1),(x2,y2),stroke=col,stroke_width=sw,stroke_linecap='round')
        if dash:line.update({'stroke-dasharray':dash})
        line.set_desc(title=f'{a} {l["a_if"]} ({l["a_ip"]}) — {b} {l["b_if"]} ({l["b_ip"]}) | {l["prefix"]}')
        d.add(line)

    for n in nodes:node_box(d,n)
    # clarity labels for selected links and multi-homing
    bubble(d,'OSPF 10',835,378,fs=13)
    bubble(d,'OSPF 10',835,890,fs=13)
    bubble(d,'dual-homed CE',212,475,fs=12)
    # CE overlapping LAN indicators are separate VRFs
    label(d,'10.100.1.0/24',28,321,12,'ca',600)
    label(d,'10.100.1.0/24',28,595,12,'cb',600)
    label(d,'OVERLAPPING IPv4, ISOLATED VRFs',40,1175,15,'ink',600)
    # legend
    yy=1199
    for x,col,t,da in [(42,colors['core'],'Preferred W1→E1',''),(395,colors['backup'],'Preferred W2→E2',''),(740,colors['rr'],'OSPF-only RR','7 6'),(1045,colors['ca'],'Customer A',''),(1315,colors['cb'],'Customer B','')]:
        kwargs={'stroke':col,'stroke_width':4}
        if da:kwargs['stroke_dasharray']=da
        d.add(d.line((x,yy),(x+57,yy),**kwargs))
        label(d,t,x+70,yy+6,14,'muted',500)
    d.save(pretty=True)
    cairosvg.svg2png(url=str(ROOT/'docs'/'topology.svg'),write_to=str(ROOT/'docs'/'topology.png'),output_width=2184,output_height=1506)


def render_links():
    # table visual companion: interface/IP link plan, including every link
    tw,th=2200,1350
    d=svgwrite.Drawing(str(ROOT/'docs'/'link-plan.svg'),size=(tw,th),viewBox=f'0 0 {tw} {th}',profile='full')
    d.add(d.rect(insert=(0,0),size=(tw,th),fill='#F7FAFD'))
    label(d,'MPLS SP ADVANCED · PHYSICAL LINKS AND IP PLAN',54,70,33,'ink',700)
    label(d,'Source of truth: docs/LINKS.csv · Interface indexing exactly matches the .unl file',54,113,19,'muted')
    def section(title, sub, x,y,width,rows):
        d.add(d.rect(insert=(x,y),size=(width,55+len(rows)*44),rx=18,fill=colors['white'],stroke='#D5E0EF',stroke_width=1.5))
        label(d,title,x+26,y+33,22,'ink',700)
        label(d,sub,x+width-22,y+32,13,'muted',400,'end')
        for i,l in enumerate(rows):
            yy=y+56+i*44
            if i%2==0:d.add(d.rect(insert=(x+7,yy),size=(width-14,44),fill='#EFF5FC'))
            ac=l['a_if'].replace('GigabitEthernet','Gi')
            bc=l['b_if'].replace('GigabitEthernet','Gi')
            label(d,f'{l["a"]} {ac}',x+25,yy+28,14,'ink',600)
            label(d,f'⇄  {l["b"]} {bc}',x+215,yy+28,14,'ink',600)
            label(d,l['prefix'],x+475,yy+28,14,'muted',400)
            marker= f'cost {l["ospf_cost"]}' if l['kind']=='core' else l.get('vrf','')
            label(d,marker,x+width-30,yy+28,14,'core' if l['kind']=='core' else ('ca' if l.get('vrf')=='CUST_A' else 'cb'),600,'end')
    core=[l for l in links if l['kind']=='core']
    ce=[l for l in links if l['kind']=='ce']
    section('MPLS / OSPF backbone','16 inter-router IP links',50,154,1150,core)
    section('PE–CE / customer VRFs','7 isolated customer links',1230,154,920,ce)
    label(d,'Address convention',1248,610,24,'ink',700)
    label(d,'Core: 172.20.<link-ID>.1–2/30',1248,663,17,'muted')
    label(d,'Customer A: 10.11.x.1 (PE) / .2 (CE)',1248,697,17,'ca')
    label(d,'Customer B: 10.12.x.1 (PE) / .2 (CE)',1248,731,17,'cb')
    label(d,'PE + P + RR Loopbacks: 10.255.0.x/32',1248,766,17,'muted')
    label(d,'Use LINKS.csv for the complete host-address mapping.',1248,825,17,'muted')
    # VRF note
    d.add(d.rect(insert=(1230,910),size=(920,260),rx=18,fill='#F0F6FE',stroke='#C9D9EF',stroke_width=1.5))
    label(d,'VRF AND ROUTE TARGETS',1250,954,22,'ink',700)
    label(d,'CUST_A  →  RT 65000:100',1250,1006,18,'ca',600)
    label(d,'CUST_B  →  RT 65000:200',1250,1053,18,'cb',600)
    label(d,'RD is unique per PE and per VRF.',1250,1101,16,'muted')
    label(d,'CE-A-W1 is dual-homed to PE-W1 and PE-W2.',1250,1133,16,'muted')
    d.save(pretty=True)
    cairosvg.svg2png(url=str(ROOT/'docs'/'link-plan.svg'),write_to=str(ROOT/'docs'/'link-plan.png'),output_width=2200,output_height=1350)

if __name__=='__main__':
    render_overview();render_links()
    print('Rendered topology.svg/png and link-plan.svg/png')
