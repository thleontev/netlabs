# Сценарии — IP Transit Multihoming

Все тесты выполнять в изолированной EVE-NG. Сначала снять `show ip bgp summary`, `show ip ospf neighbor`, RIB, ICMP/trace, после — сравнить и вернуть конфигурации.

## 00. Baseline
- PE1/PE2/CORE-RR: **3 OSPF линка**; CORE-RR: **2 iBGP neighbors**.
- В сети **6 eBGP линков**: PE1–ISP-A, PE2–ISP-B, ISP-A–INET, ISP-B–INET, PE1–CE-A, PE2–CE-A.
- HOST-A `ping 198.51.100.10`, EXT-HOST `ping 203.0.113.10`. Записать AS_PATH, Local Preference, next-hop.

## 01. Upstream A down
- На PE1: `conf t` → `interface Gi0/2` → `shutdown` → `end`.
- Проверить маршрут через ISP-B и PE2, восстановление связности. На PE1 возможен транзит через OSPF core.
- Откат: `interface Gi0/2` → `no shutdown`.

## 02. Клиентский uplink PE1–CE-A down
- На CE-A `interface Gi0/0` → `shutdown`.
- Должен остаться eBGP CE-A ↔ PE2; PE1 получит путь клиента через RR.
- Проверить двусторонний ICMP; откат `no shutdown`.

## 03. Ошибочный анонс / prefix filtering
- CE-A: `interface Loopback99`, `ip address 192.0.2.254 255.255.255.0`.
- CE-A: `router bgp 65010`, `network 192.0.2.0 mask 255.255.255.0`.
- Убедиться, что PE1/PE2 **не принимают** `192.0.2.0/24` через `PFX_CLIENT_A`, несмотря на локальную BGP-таблицу CE-A.
- Откатить `no network 192.0.2.0 mask 255.255.255.0`, `no interface Loopback99`. **Не** выключать защиту на внешних стыках.

## 04. BGP path selection
- Измерить на PE2 Local Preference двух путей к `198.51.100.0/24`.
- На PE1 удалить входящую `neighbor 10.10.0.2 route-map PREFER_ISP_A in`, затем `clear ip bgp 10.10.0.2 soft in`. Compare RIB на PE1/PE2.
- Восстановить route-map, выполнить soft inbound refresh. Дополнительно: проверить, почему Local Preference имеет приоритет над AS_PATH и почему inbound traffic не контролируется одной вашей AS.

## 05. OSPF failover / adjacency
- PE1 Gi0/0 `shutdown` → CORE-RR остаётся доступным через PE2 и прямую связь PE1–PE2.
- Вернуть `no shutdown`.
- Дополнительно: на PE1 Gi0/0 выполнить `ip ospf 100 area 1` и наблюдать mismatch с CORE-RR. Откат `no ip ospf 100 area 1`.

## 06. VRF isolation
- PE1: `show ip vrf interfaces`, `show ip route vrf CUST_B`.
- PE1: `ping vrf CUST_B 192.0.2.10 source 10.20.0.9` — должен ответить HOST-B.
- Глобальный `show ip route 192.0.2.10` — не содержит CUST_B LAN. HOST-B не должен достигать EXT-HOST без осознанного route leaking.

## 07. Filter failure (BGP Established ≠ forwarding)
- PE2: `ip prefix-list BAD_EXT seq 5 permit 192.0.2.0/24`.
- В `router bgp 65000` заменить `neighbor 10.10.0.6 prefix-list PFX_EXT in` на `neighbor 10.10.0.6 prefix-list BAD_EXT in`, затем `clear ip bgp 10.10.0.6 soft in`.
- BGP сессия остаётся Established, route от ISP-B отфильтрован; при активном ISP-A ICMP может работать через альтернативу.
- Откат `neighbor 10.10.0.6 prefix-list PFX_EXT in` и `no ip prefix-list BAD_EXT`.

## 08. Контрольный incident response
Другой участник ломает одну из настроек (BGP neighbor AS, prefix-list, OSPF area, интерфейс, next-hop); инженер за **30 минут** находит root cause, устраняет и оформляет RCA: symptoms, observations, action, rollback, verification. Успех — восстановленная связность с доказательствами, а не просто `ping`.
