# Исторические VXLAN Flood & Learn и PIM BIDIR: что было и зачем изучать

**Источник:** https://github.com/thleontev/netlabs/tree/main/gns3/VXLAN

- `VXLAN Topology 2 (F&L)`: NX-OS Titanium 7.3, OSPF underlay, PIM sparse-mode на физических и loopback-интерфейсах, RP `10.1.10.2`, multicast group `224.1.1.10/20/30` для VNI 10010/10020/10030. Отдельного BGP EVPN хостового control plane нет; VTEP learns MAC через VXLAN data plane / flood.
- `VXLAN Topology 2_1 (F&L BIDIR)`: та же архитектура, RP команда содержит `bidir`. Это **не** синоним ingress replication; это multicast routing mode, где отличия PIM дерева меняют BUM доставку.
- `VXLAN Topology 3_1 (EVPN)`: старый учебный конфиг одновременно содержит `host-reachability protocol bgp` и `mcast-group` под L2 VNI. Это допустимое сочетание control-plane MAC signaling (EVPN) и multicast репликации BUM. **Не смешивать два независимых вопроса: как VTEP узнаёт о MAC? как доставляет BUM?**
- Новый пакет использует **BGP EVPN + head-end ingress replication**, где BGP Type-3 IMET даёт VTEP flood-list. Для проверки инкапсуляции трафик UDP/4789 идёт через spine без multicast PIM, что упрощает изучение BGP и L3 VRF.

## План отдельного упражнения по старой модели

1. Поднять stage00 с OSPF и добиться Lo1↔Lo1 reachability.
2. Удалить/не запускать BGP EVPN; включить на Cisco `feature pim`, PIM-SM на обоих underlay interfaces, loopback underlay и VTEP loopback в соответствии с официально поддерживаемой версией NXOSv.
3. Поднять RP, например на spine (проверить SSM/ASM и при двух RP наличие корректного anycast RP / MSDP или иной поддерживаемой схемы). Прописать RP на всех VTEP, связать VNI с multicast-group.
4. Сравнить PIM multicast forwarding `show ip mroute`, `show ip pim neighbor`, `show ip pim rp`, NVE peer, MAC learning, пинги и traffic capture.
5. Для варианта BIDIR убедиться, что **все** узлы и версия образа поддерживают PIM BIDIR, и применить согласованный `bidir` RP/группы на всём пути. Не ограничиваться изменением одной команды RP на одном leaf.
6. Сравнить артефакты проверки: Flood & Learn → data-plane learn; EVPN → control-plane Type-2 MAC/IP, Type-3 IMET; Type-5 / symmetric IRB появляется на L3 EVPN.

**Состояние:** это специально **отдельный сценарий для ручной реализации**, а не заявленная как готовая протестированная конфигурация Flood & Learn. Для старой PIM ветки желательно использовать фактические 7.3 и 9.3 конфиги старого репозитория и проверять поддержку на имеющемся Nexus 9000v.
