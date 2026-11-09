# Как диагностировать MPLS L3VPN: сверху вниз

## 1. Физика / L3

`show ip interface brief`, `show interfaces description`, `show ip ospf neighbor`, `show ip route <remote-PE-loopback>`. Наличие IP-доступности не доказывает существование LDP-меток и корректность VPN.

## 2. IGP

`show ip ospf interface`, `show ip ospf database router`, `show ip route ospf`, `show ip cef <remote-PE-loopback> detail`. Сопоставляйте стоимость пути с `LINKS.csv`, а не с расстоянием на картинке.

## 3. LDP/MPLS transport

`show mpls interfaces`, `show mpls ldp neighbor`, `show mpls ldp bindings`, `show mpls forwarding-table`. LDP требуется на транзитных P/PE линках, **не на RR и не на PE–CE**. При PHP penultimate hop может отправить IP packet после снятия transport label, но VPN label сохраняется до egress PE; поведение зависит от назначения меток и функций платформы.

## 4. MP-BGP VPNv4

`show ip bgp vpnv4 all summary`, `show ip bgp vpnv4 all`, `show ip bgp vpnv4 all labels`. У PE VPNv4-соседи RR1/RR2, а не другие PE. Route Reflector должен сохранять next-hop PE и передавать extended communities для RT.

## 5. VRF / PE–CE

`show ip vrf`, `show ip route vrf CUST_A`, `show ip bgp vpnv4 vrf CUST_A`, `show ip bgp vpnv4 vrf CUST_B`, `show ip bgp neighbors <CE-IP>` (для выбранной AF соответствующие команды IOS). Проверяйте: адрес интерфейса во VRF, RD, RT import/export, статус CE eBGP, BGP next-hop, local-pref и источник маршрута.

## 6. End-to-end

С `CE-A-W1`: `ping 10.100.4.1 source Loopback0`, с `CE-B-W`: `ping 10.100.3.1 source Loopback0`. Оба должны иметь свои VPN пути. Изолированность проверяется по уникальным customer-A префиксам, а не по совпадающим /24.

## Типичные ошибки

| Симптом | Где искать |
|---|---|
| PE loopback не доступен | OSPF adjacency/cost/ACL/IP, loopback OSPF passive |
| OSPF есть, LDP нет | `mpls ip`, router-id, LDP TCP/UDP 646, интерфейс |
| VPNv4 established, маршрут отсутствует | CE BGP `network`, импорт RT, RD, outbound RT propagation |
| На RR prefix есть, на PE нет | RT import, vpnv4 next-hop reachability, label to egress PE |
| CE видит prefix, но data plane blackhole | transport label LFIB, VPN label, wrong vrf, MTU |
| После падения первичного CE линка нет резервного пути | BGP convergence, CE-W1 second neighbor, RR reflections, PE-W2 VRF |
| CUST_B видит CUST_A-only prefix | импорт чужого RT, несоответствие VRF или конфигурации PE |

Не опирайтесь на абсолютные номера MPLS меток и фиксированное время сходимости: они зависят от версии образа/порядка старта.
