# VXLAN EVPN: краткая карта диагностики сценариев

Работать от L1/L3 к overlay, а не наоборот. Сценарии: [индекс](../scenarios/README.md).

| Симптом | Первое подозрение | Подтверждение |
|---|---|---|
| Ни один VTEP Lo1 недоступен | underlay OSPF / link | `show ip ospf neighbors`, `show ip route 10.254.0.23` |
| BGP Established, VTEP недоступен | Lo1 не в IGP, underlay ACL/MTU | `ping 10.254.0.23 source 10.254.0.21`; `show nve peers` |
| Нет EVPN peer RR | Lo0 underlay / BGP config | `show bgp l2vpn evpn summary` |
| Только один VLAN не работает | VNI/RT, Type-2/3, BUM | `show running-config evpn`, `show nve vni`, `show bgp l2vpn evpn` |
| После прогрева всё работает, новые ARP нет | BUM flood list / ingress replication | Type-3 IMET, packet capture UDP/4789 |
| Same-subnet ping работает, меж VLAN нет | SVI/Anycast/L3VNI | `show interface Vlan30`, `show ip route vrf TENANT1` |
| Type-5 виден локально, удалённая VRF пустая | RT import, route-type, next-hop | `show bgp l2vpn evpn`, `show ip route vrf CLIENTS` |
| Локальная статика есть, Type-5 не приходит | BGP redistribution | `show running-config bgp`, `show ip route vrf CLIENTS` |
| Маршрут в двух VRF, но доступ не проходит | RT leak / next-hop / asymmetric path | extended communities и packet path |
| Inter-VRF ping пропал, VNI работает | firewall forwarding/rule/return route | `tcpdump`, `nft list ruleset`, `ip route` |
| Маленький ping работает, большой нет | MTU/PMTUD/fragmentation | Linux ping DF, underlay capture UDP/4789 |

## Слои и порты

- **Underlay**: IPv4 /31, OSPF IP protocol 89, Loopback0 (BGP) и Loopback1 (VTEP) /32.
- **BGP EVPN control plane**: TCP/179 между Loopback0 Leaf и Spine RR.
- **VXLAN data plane**: UDP/4789 outer src/dst VTEP Loopback1, внутри исходный Ethernet frame; L2 VNI и L3 VNI — разные dataplane контексты.
- **Firewall service path**: LEAF-02 Ethernet1/5 (VRF CLIENTS / 172.31.10.1/30) и Ethernet1/6 (VRF APPS / 172.31.20.1/30).

## Эталонные данные из README

- SPINE Lo0: `10.255.0.11`, `10.255.0.12`.
- LEAF Lo0: `10.255.0.21`–`.23`.
- LEAF Lo1/VTEP: `10.254.0.21`–`.23`.
- L2 VNI: `10010`, `10020`, `10030`.
- Stage02 VRF TENANT1, L3 VNI `50001`.
- Stage03 CLIENTS L3 VNI `50110`, APPS L3 VNI `50220`.
- Firewall next-hops: `172.31.10.2` в CLIENTS и `172.31.20.2` в APPS.

## Шаблон отчёта

| Поле | Что записать |
|---|---|
| Scenario / Stage | ID, config stage, NX-OS version |
| Time initiated | фактическая отметка времени |
| Expected | предсказанные control/data plane состояния |
| Observed | 2+ CLI вывода и 1 traffic probe |
| Path before / after | исходящий и обратный path |
| Root cause | конкретная ошибка маршрутизации/policy/VNI |
| Rollback | точные команды, время отката |
| Time recovered | наблюдаемая, а не выдуманная сходимость |

**Важное ограничение:** команды основаны на текущих конфигурациях репозитория; образ NX-OSv 9.3(x) на реальном стенде не проверялся. В случае отличий проверь `?` в CLI, сохрани вывод и обнови сценарий с указанием версии.
