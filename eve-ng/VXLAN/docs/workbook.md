# Практикум VXLAN EVPN: повторяем, а не просто копируем конфигурацию

Не начинать следующий этап, пока не выполнены критерии текущего. Перед вставкой полного CFG: сохранить `show running-config`, очистить тестовое состояние либо вручную удалять остатки предыдущей стадии.

## 00 — Underlay: OSPF + dual spine

**Вспомнить:** L3 Leaf–Spine, ECMP, OSPF P2P, transit links /31, loopback /32, VTEP IP должен быть маршрутизируем с underlay. Spine не соединяются между собой — каждый Leaf является транзитом между ними (проверь, нужен ли такой трафик).

- Самостоятельно выбрать и настроить Lo0, Lo1, 6 x /31, OSPF area 0 (подсказка: `docs/` содержит addressing в README).
- До проверки открыть `configs/00-underlay` только как эталон.
- На LEAF-01: `show ip ospf neighbors` — **2** FULL; SPINE-01 — **3** FULL; LEAF-01 → Lo1 LEAF-03 — ping успешен.
- На LEAF-01: `show ip route 10.254.0.23` — в таблице два равнозначных пути (если версия и настройки NX-OS позволяют ECMP).
- BREAK #1: отключить L1 E1/1, проверить сохранение ping Lo1 через S2, восстановить.
- BREAK #2: выключить оба underlay порта LEAF-03, локализовать отказ по neighbor, route, pings, потом восстановить.

**Объяснить письменно:** зачем BGP peer через Lo0, VXLAN src через Lo1? Что произойдёт, если Lo1 не объявлять в OSPF?

## 01 — EVPN L2: Route Type 2, 3 и BUM

**Вспомнить:** VLAN (локальный), L2VNI (глобальный), RD (уникальность NLRIs), RT (политика import/export), VTEP (внешний IP), IMET Type-3, MAC/IP Type-2; MAC-learning local vs remote; ARP broadcast; head-end ingress replication вместо PIM multicast.

- Развернуть `configs/01-evpn-l2` в чистой лаборатории. Сначала — SPINE RR, затем leaf, затем VPCS. Проверить 2 RR-соседа на каждом leaf: `show bgp l2vpn evpn summary`.
- `show nve vni` — только **два локально присутствующих VNI** на каждом leaf (10010/10020 на L1, 10010/10030 на L2, 10020/10030 на L3); `show nve peers` — ожидаются 2 peer VTEP. Пусто до появления overlay-сессий/активности на некоторых образах — свериться с `show bgp l2vpn evpn`.
- На VPCS `CLIENT-A ping 192.168.10.12`; аналогично APP-A→APP-C и DB-B→DB-C. Меж VLAN10 и VLAN20 ping **не должен** проходить.
- После ping на Leaf найти `show mac address-table vlan 10`, `show l2route evpn mac all`, `show bgp l2vpn evpn`; сравнить локальную MAC и remote MAC.
- BREAK #3: на LEAF-03 изменить RT export/import **только** VNI10020 (например `route-target import 65000:9999`), проверить APP-A↔APP-C, при этом VLAN10 остаётся работающим; откатить.
- BREAK #4: убрать `ingress-replication protocol bgp` для VLAN30 только на одном Leaf; выяснить, почему ICMP/ARP может работать нестабильно, чего не хватает в BUM flood list.
- BREAK #5: shut SPINE-01, убедиться, что RR SPINE-02 продолжает обмен маршрутами EVPN; замерить восстановление с `show bgp l2vpn evpn summary`.

**Объяснить письменно:** чем Type-3 отличается от Type-2? Чем multicast F&L отличается от BGP ingress replication? Где UDP/4789? Почему RD и RT — разные сущности?

## 02 — Symmetric IRB + Anycast Gateway

**Вспомнить:** distributed anycast gateway IP+MAC, IP-VRF, L3VNI, Type-5 IP Prefix route, symmetric/asymmetric IRB, routing между разными L2VNI, разница между `interface Vlan10` и L3VNI VLAN500.

- Чисто загрузить `configs/02-symmetric-irb`; задать default gateway в VPCS по файлу `VPCS-commands.txt`.
- CLIENT-A ping 192.168.10.1, затем APP-C 192.168.20.13, **DB-C 192.168.30.13**. Последний тест должен использовать L3VNI, потому что LEAF-01 не имеет локальной VLAN30.
- Проверить `show ip route vrf TENANT1`, `show nve vrf`, `show ip arp vrf TENANT1`, `show bgp l2vpn evpn` и наличие Type-5 для сетевых префиксов (подтвердить по реальной версии NX-OS).
- BREAK #6: удалить/заменить anycast gateway MAC только на LEAF-03, сравнить ARP/MAC и меж-VLAN маршрут. Восстановить одинаковую MAC на всех leaf.
- BREAK #7: нарушить L3VNI RT импорт на LEAF-01, проверить, какие маршруты и трафик пропали, отличить от L2 VNI аварии.

**Объяснить письменно:** зачем отдельный L3VNI? В каких случаях трафик может идти L2 VXLAN, а когда — через симметричный L3 IRB? Почему одинаковый IP шлюза на разных Leaf — допустим?

## 03 — CLIENTS / APPS VRF + Firewall

**Вспомнить:** VRF isolation, VLAN→VNI→VRF mappings, L3VNI per VRF, external PBR/FW service insertion vs route leaking, статическая маршрутизация через firewall, распространение Type-5 из border leaf, stateful inspection.

- Использовать отдельную топологию `VXLAN-FABRIC-MULTITENANT-FW.unl`: те же 5 Nexus + 6 VPCS и FW-LINUX.
- Полностью настроить clean nodes из `configs/03-multitenancy-fw`; на LEAF-02 проверить доступность напрямую подключенных next hops FW в **двух разных VRF**.
- В Debian FW посмотреть `ip -br link`, установить `iproute2, nftables, tcpdump`, применить `scripts/fw-setup.sh` с правильными env-переменными.
- Без Firewall или с отключённым его IP forwarding CLIENT-A → APP-C должен быть **недоступен**; CLIENT-A → CLIENT-B и APP-A → APP-C работают.
- С Firewall и ICMP allow CLIENT-A → APP-C начинает проходить, при этом TCP соединения между зонами по умолчанию блокируются. Контролировать счетчики `nft list ruleset`.
- BREAK #8: удалить статический маршрут `192.168.20.0/24` из VRF CLIENTS LEAF-02: что происходит с Type-5 и ping?
- BREAK #9: отключить `redistribute static route-map RM_FIREWALL` на LEAF-02: маршрут остаётся локально, но удаляется из EVPN; проверить на LEAF-01.
- BREAK #10: поменять VNI/RT только у VRF APPS на одном leaf и доказать локализацию через `show nve vrf` и BGP.

**Объяснить письменно:** почему прямой RT route leaking CLIENTS↔APPS обходит межсетевой экран? Какие маршруты должны анонсироваться как Type-5? Почему firewall должен знать обратные маршруты? Как отсечь одной политикой все клиентские VLAN?

## Сетка оценки результата

| Навык | Проверка | Готово |
|---|---|---|
| OSPF/ECMP | 2 OSPF peers на Leaf, 3 на Spine, Lo1 ping при отказе одного линка | ☐ |
| EVPN L2 | 3 пары VPCS внутри одного VLAN проходят, между VLAN нет | ☐ |
| EVPN control | Type-2/Type-3 в `show bgp l2vpn evpn`, понятен RD/RT/VNI | ☐ |
| IRB | Меж VLAN ICMP в одном VRF, шлюз anycast одинаковый | ☐ |
| Multitenancy | Inter-VRF фильтруется FW, не возникает прямого route leak | ☐ |
| Troubleshooting | 5+ намеренно внесённых сбоев найдены и исправлены | ☐ |

## Команды для мини-шпаргалки

```
show ip ospf neighbors
show ip route 10.254.0.23
show bgp l2vpn evpn summary
show bgp l2vpn evpn
show nve interface 1 detail
show nve peers
show nve vni
show nve vrf
show l2route evpn mac all
show l2route evpn mac-ip all
show ip arp vrf TENANT1
show ip route vrf TENANT1
show ip route vrf CLIENTS
show ip route vrf APPS
show running-config interface nve1
```
