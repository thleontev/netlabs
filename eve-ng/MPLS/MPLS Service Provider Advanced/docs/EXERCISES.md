# MPLS SP Advanced — программа занятий

Весь комплект создан для **EVE-NG Community**, Cisco IOSv. Фазы 00/01/02 — полные конфигурации узлов, а не патчи. Не применять на действующем оборудовании.

| № | Занятие | Действие | Критерий успеха |
|---|---|---|---|
| 1 | Топология/IP | Запустить 16 узлов; загрузить `00-underlay`; сверить `LINKS.csv` | 23 link сети, loopback маршрутизаторов доступны из PE; соседства OSPF на 16 core линках |
| 2 | Underlay/IGP | Изучить cost 10/20/30/35, вычислить два пути | На PE-W1 до PE-E1 loopback через P1→P3; суммарная OSPF-стоимость 30 в модели |
| 3 | Отказ SPF | Shutdown P1–P3; замерить outage ICMP | CE маршрутизация в underlay не включена, но PE loopback `10.255.0.3` остаётся достижимым |
| 4 | MPLS транспорт | Загрузить `01-ldp`; проверить LDP neighbors, LFIB | LDP established между P/PE, label switching для удалённых loopback; RR не LDP-пир |
| 5 | PHP/метки | Включить `debug mpls packets` только при малой нагрузке (если доступно) или `traceroute`/`show mpls forwarding-table` | Убедиться, где выполняется swap и penultimate-hop popping; метки динамические, цифры не фиксировать |
| 6 | Route Reflectors | Загрузить `02-l3vpn`, анализ VPNv4 peerings | На RR1 и RR2 по четыре VPNv4 клиента, на каждом PE два RR-пира; оба RR не являются транзитными LSR |
| 7 | VRF/RD/RT | Сравнить RD/RT на четырёх PE | RT совпадает по клиентам, RD различаются для каждого PE/VRF (всего восемь RD) |
| 8 | CE–PE BGP | Проверить семь eBGP сессий PE–CE | Все `Established`; в CUST_A четыре LAN префикса, CUST_B два (всё с учетом особенностей bestpath) |
| 9 | Перекрывающиеся сети | `CE-A-W1` и `CE-B-W` оба владеют `10.100.1.0/24` | Между VRF нет автоматического route leaking; CE_A/E и CE_B/E достигаются строго в своих VPN |
| 10 | Dual-homing | На CE-A-W1 проверить eBGP с PE-W1/W2, local-pref 200 на PE-W1; отключить primary | CE-A-W1 ↔ CUST_A remote LAN остаётся работоспособным после convergence через PE-W2 |
| 11 | RR high availability | Выключить RR1 (не core) | С RR2 VPNv4 control plane сохраняется; при восстановлении RR1 сессии возвращаются |
| 12 | VRF import policy | Сломать RT CUST_A на PE-E2, затем исправить | Маршруты исчезают на одном PE только для заданного VPN; после восстановления импортируются |
| 13 | Route leaking | Намеренно импортировать RT CUST_A в CUST_B на PE-W1 | Появляется чужой маршрут `10.100.4.0/24`; определить нарушение изоляции, затем откатить |
| 14 | IGP re-optimization | Вручную поднять OSPF cost на линке PE-W1→P1 | Смена пути через P2 подтверждается `show ip route` + `show mpls forwarding-table` |
| 15 | Fault isolation | Сценарии `scenarios/FAULTS.md` выполнять без предварительного просмотра диагноза | Зафиксировать симптом, гипотезу, show, исправление, проверку на клиентском ping |

## Базовые команды

На P/PE/RR:

```text
show ip ospf neighbor
show ip ospf interface brief
show ip route 10.255.0.3
show ip cef 10.255.0.3 detail
```

На P/PE (но не RR):

```text
show mpls interfaces
show mpls ldp neighbor
show mpls ldp bindings
show mpls forwarding-table
```

На PE:

```text
show ip vrf
show ip route vrf CUST_A
show ip route vrf CUST_B
show ip bgp vpnv4 all summary
show ip bgp vpnv4 vrf CUST_A
show ip bgp vpnv4 all labels
```

На RR:

```text
show ip bgp vpnv4 all summary
show ip bgp vpnv4 all
```

На CE:

```text
show ip bgp summary
show ip bgp
ping 10.100.4.1 source Loopback0
```

**Важно:** не делайте вывод об изоляции VPN по одному ping на совпадающий IP. Проверяйте таблицы VRF и *уникальные* адреса `10.100.2.1`/`10.100.4.1`, отсутствующие у CUST_B. У CUST_A сеть `10.100.3.0/24` относится к CE-A-E1, у CUST_B — к CE-B-E, и это задуманный overlap.

## Критерии готовности

Зафиксировать: вывод соседств OSPF и LDP, таблицы LFIB для одного FEC, VPNv4 route с меткой/RT, список BGP peerings, изменение маршрута после отказа P1–P3 и PE-W1 CE линка, время восстановления клиентского потока. Для времени конвергенции отправляйте регулярные ICMP-пакеты с CE; не утверждайте значение RTO без измерения.
