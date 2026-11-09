# VXLAN — лаборатории EVE-NG

Коллекция независимых лабораторий VXLAN для EVE-NG Community Edition. Каждая лаборатория находится в собственной папке с топологией, конфигурациями, практическими сценариями и документацией.

## [VXLAN-FABRIC](VXLAN-FABRIC/README.md)

Учебная **Leaf–Spine VXLAN EVPN fabric**: 2 Spine (BGP EVPN Route Reflector), 3 Leaf (VTEP) и 6 VPCS. В лаборатории изучаются OSPF underlay, EVPN L2, BUM/ingress replication, Anycast Gateway, Symmetric IRB, L3VNI, Multitenancy и отказоустойчивость.

### Топология

![VXLAN EVPN Leaf–Spine: 2 Spine, 3 Leaf, 6 VPCS](VXLAN-FABRIC/vxlan-fabric-topology.png)

[Открыть SVG](VXLAN-FABRIC/vxlan-fabric-topology.svg) · [Вариант с firewall (PNG)](VXLAN-FABRIC/vxlan-multitenant-fw-topology.png) · [SVG с firewall](VXLAN-FABRIC/vxlan-multitenant-fw-topology.svg)

### Варианты лаборатории

| Топология EVE-NG | Назначение |
|---|---|
| [VXLAN-FABRIC-5N-6H.unl](VXLAN-FABRIC/VXLAN-FABRIC-5N-6H.unl) | Базовая фабрика с EVPN L2 |
| [VXLAN-FABRIC-MULTITENANT-NOFW.unl](VXLAN-FABRIC/VXLAN-FABRIC-MULTITENANT-NOFW.unl) | Две VRF без межсетевого экрана |
| [VXLAN-FABRIC-MULTITENANT-IOSV-FW.unl](VXLAN-FABRIC/VXLAN-FABRIC-MULTITENANT-IOSV-FW.unl) | Меж-VRF маршрутизация через IOSv с ACL |
| [VXLAN-FABRIC-MULTITENANT-FW.unl](VXLAN-FABRIC/VXLAN-FABRIC-MULTITENANT-FW.unl) | Меж-VRF маршрутизация через Linux firewall |

### Материалы

- [Конфигурации 00–03](VXLAN-FABRIC/configs/) — OSPF, EVPN L2, Symmetric IRB, Multitenancy.
- [Практикум](VXLAN-FABRIC/docs/workbook.md) и [13 сценариев диагностики](VXLAN-FABRIC/scenarios/README.md) — отказ линка, RR, VTEP, RT/VNI, Type-5, firewall и MTU.
- [Диагностическая карта](VXLAN-FABRIC/docs/SCENARIO-DIAGNOSTICS.md) и [инструкция по импорту](VXLAN-FABRIC/docs/STARTUP-CONFIG-REPAIR.md).

**Важно:** для NX-OS нужны соответствующие QEMU-образы. В `.unl` предусмотрены встроенные startup-config, но их применение и фактическая работа зависят от версии EVE-NG CE и образов. Linux-вариант требует отдельного образа, а IOSv с ACL — не stateful firewall.

Другие VXLAN-лаборатории размещаются отдельными папками рядом с `VXLAN-FABRIC/`.
