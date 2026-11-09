# Диагностика IP Transit

## Packet journey
Сверяйте **interface → IPv4 → OSPF → BGP state → accepted/advertised prefixes → best-path → next-hop → RIB/FIB → forwarding**.

| Вопрос | Cisco IOSv |
| --- | --- |
| Физика/IP | `show ip interface brief`, `show interfaces description` |
| OSPF | `show ip ospf neighbor`, `show ip route ospf`, `show ip protocols` |
| BGP peers | `show ip bgp summary`, `show ip bgp neighbors <peer>` |
| Префикс/AS-PATH | `show ip bgp 198.51.100.0`, `show ip bgp 203.0.113.0` |
| Выходящие анонсы | `show ip bgp neighbors <peer> advertised-routes` (синтаксис может зависеть от образа) |
| Next-hop и FIB | `show ip route <destination>`, `show ip cef <destination>` |
| VRF | `show ip vrf interfaces`, `show ip route vrf CUST_B` |
| Сегмент end-to-end | `traceroute <dest>`, `ping <dest> source <src>` |

## Ожидаемая политика
- Внешняя сеть AS65300 объявляет только `198.51.100.0/24`.
- Клиент AS65010 объявляет только `203.0.113.0/24`.
- PE1 принимает upstream-A путь с `local-preference 200`; через route reflector PE2 может предпочесть путь через PE1 даже при своём прямом eBGP к ISP-B.
- INET-SIM предпочитает маршрут к клиенту через ISP-A (Local Preference 200).
- CE-A предпочитает PE1 через `weight 200` (локальный Cisco-атрибут, не передаётся в BGP UPDATE).
- CE-B — отдельная VRF-Lite на PE1; глобальная таблица не содержит её LAN.
- BGP `Established` не доказывает наличие маршрута в RIB/FIB.

## RCA template
```text
Incident:
Start / end:
Impact:
Evidence before change:
Root cause:
Fix:
Evidence after change:
Rollback:
Prevention:
```
