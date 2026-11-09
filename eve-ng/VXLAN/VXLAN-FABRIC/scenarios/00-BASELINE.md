# 00 — Базовый маршрут пакета, control plane и data plane

**Этапы:** 00, 01, 02, 03 — по отдельности, с чистым запуском каждой стадии.

## Stage 00: IP/OSPF

- LEAF-01: `show ip ospf neighbors` — 2 FULL, SPINE-01 — 3 FULL.
- LEAF-01: `show ip route 10.254.0.23`; `ping 10.254.0.23 source 10.254.0.21`. Путь к удалённому VTEP должен существовать, по возможности с 2 ECMP next-hop.
- В capture на link Leaf↔Spine можно обнаружить OSPF; VXLAN UDP/4789 на этом этапе ещё отсутствует.

## Stage 01: L2 EVPN

- LEAF-01: `show bgp l2vpn evpn summary`: оба RR 10.255.0.11/12 Established.
- LEAF-01: `show nve vni`, `show nve peers`, `show l2route evpn mac all`, `show bgp l2vpn evpn`.
- VPCS: CLIENT-A (192.168.10.11) → CLIENT-B (192.168.10.12), APP-A (192.168.20.11) → APP-C (192.168.20.13), DB-B (192.168.30.12) → DB-C (192.168.30.13) должны работать; CLIENT-A → APP-C **не должен**.
- Сначала очисти старую ARP-информацию ожиданием истечения кэша или перезапуском тестового VPCS. После нового ARP сравни Type-3 (IMET/BUM) и Type-2 (MAC/IP).
- Захват на uplink Leaf↔Spine: `udp port 4789` у data plane, `tcp port 179` у BGP EVPN. Spine — L3 transit + RR, **не** VTEP.

## Stage 02: L3 EVPN / Symmetric IRB

- CLIENT-A (192.168.10.11) → DB-C (192.168.30.13) при установленном gateway. Локального VLAN30 на LEAF-01 **нет**: путь проходит через L3 VNI 50001.
- LEAF-01: `show ip route vrf TENANT1`, `show nve vrf`, `show bgp l2vpn evpn` (отдельно проверить присутствие/атрибуты Type-5, если образ использует их для этих сетей).
- Выясни, на каком leaf выполняется входной IRB, где IP-VRF, а где обычный L2VNI forwarding.

## Stage 03: inter-VRF through firewall

- Схема `VXLAN-FABRIC-MULTITENANT-FW.unl`, конфиги `03-multitenancy-fw`, Linux firewall настроен отдельно (два routed интерфейса к LEAF-02).
- Внутри CLIENTS и APPS ожидается доступность; между VRF без работы FW связь должна отсутствовать.
- LEAF-02: `show ip route vrf CLIENTS`, `show ip route vrf APPS`. На FW: `ip route`, `sysctl net.ipv4.ip_forward`, `nft list ruleset`, `tcpdump`.
- Зафиксировать путь **в обе стороны** и число переходов через firewall; Type-5, RT и статические маршруты смотреть отдельно.

## Мини-отчёт

| Stage | Src → Dst | Control plane | Data plane | Expected | Observed |
|---|---|---|---|---|---|
| 00 | LEAF-01 Lo1 → LEAF-03 Lo1 | OSPF | native IP | reachable | |
| 01 | CLIENT-A → CLIENT-B | EVPN Type-2/3 | L2VNI 10010 | reachable | |
| 01 | CLIENT-A → APP-C | EVPN L2 only | no IP routing | isolated | |
| 02 | CLIENT-A → DB-C | EVPN + VRF Type-5 | L3VNI 50001 | reachable | |
| 03 | CLIENT-A → APP-C | EVPN, inter-VRF static | FW | policy-dependent | |

Сравнить этот baseline с DDoS: маршрутом управляют BGP/GRE; с MPLS: LDP/VPNv4. В VXLAN BGP может быть здоров, а UDP/4789 не доставляться.
