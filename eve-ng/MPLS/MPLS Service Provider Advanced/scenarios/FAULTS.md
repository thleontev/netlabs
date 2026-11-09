# Break/Fix: аварийные сценарии

**Применяйте только в лаборатории EVE-NG после загрузки `configs/02-l3vpn` и проверки стабильности сети.** Команды даны для named interfaces, которые можно проверить в `docs/LINKS.csv`. Указанные последствия являются ожидаемой гипотезой; реальные симптомы зависят от IOSv и таблиц переадресации.

## F01. Разрыв магистрали P1↔P3

На `P1` (этот линк — `GigabitEthernet0/3`, `172.20.6.1/30`):

```text
conf t
interface GigabitEthernet0/3
 shutdown
end
```

Ожидаем: OSPF-соседство P1↔P3 исчезнет; SPF перестроит путь от PE-W1 к PE-E1; VPNv4 RR сессии не должны пропадать из-за обрыва одной магистрали. Тест: регулярный ping `CE-A-W1` → `10.100.4.1` и `show ip route 10.255.0.3` на PE-W1. Откат: `no shutdown` на том же интерфейсе.

## F02. LDP сломан, OSPF работает

На `P3`, `GigabitEthernet0/0` (к P1):

```text
conf t
interface GigabitEthernet0/0
 no mpls ip
end
```

Ожидаем: соседство LDP по данному линку теряется; IP/OSPF продолжает работать. Возможен blackhole VPN data plane при выбранном IGP next-hop без совместимого transport label. Это именно эксперимент: перед тестом снимите `show mpls ldp neighbor`, `show mpls forwarding-table` и `show ip cef 10.255.0.1`. Откат: `mpls ip` на интерфейсе.

## F03. Отказ Route Reflector RR1

На `P1`, `GigabitEthernet0/5` (к RR1):

```text
conf t
interface GigabitEthernet0/5
 shutdown
end
```

Ожидаем: BGP VPNv4 пиры PE→RR1 теряются; PE→RR2 остаются. VPN сервис восстанавливается/сохраняется при наличии маршрутов от RR2. Откат: `no shutdown`.

## F04. Нарушение импортной политики VRF A

На `PE-E2`:

```text
conf t
ip vrf CUST_A
 no route-target import 65000:100
 route-target import 65000:999
end
```

На PE-E2 маршруты удалённых CUST_A площадок пропадут из VRF. Проверить `show ip bgp vpnv4 vrf CUST_A` и `show ip route vrf CUST_A`. Откат:

```text
conf t
ip vrf CUST_A
 no route-target import 65000:999
 route-target import 65000:100
end
```

## F05. Dual-homed CE теряет основной PE

На `PE-W1`, линк к `CE-A-W1` — `GigabitEthernet0/2`:

```text
conf t
interface GigabitEthernet0/2
 shutdown
end
```

Проверить eBGP и ping с CE-A-W1 на `10.100.4.1 source Loopback0`. После BGP сходимости второе подключение к `PE-W2` должно сохранить связь. На RR посмотреть обновление best path для RD/префикса `10.100.1.0/24`. Откат: `no shutdown`.

## F06. Принудительная смена MPLS транспорта через OSPF cost

На `PE-W1`, Gi0/0 (к P1):

```text
conf t
interface GigabitEthernet0/0
 ip ospf cost 120
end
```

Ожидаем основной shortest path к удалённому PE через P2 вместо P1; проследить изменение RIB/CEF/LFIB. Откат: `ip ospf cost 10`.

## F07. Ошибка изоляции VPN — случайный route leaking

На `PE-W1`, внутри VRF B **намеренно** импортировать route target VPN A:

```text
conf t
ip vrf CUST_B
 route-target import 65000:100
end
```

После обновления маршрутов B на PE-W1 может получить чужие *неперекрывающиеся* A-only сети, например `10.100.4.0/24`. Проверить `show ip route vrf CUST_B 10.100.4.0` и таблицу BGP VRF: уже само присутствие чужого префикса доказывает утечку. **Ping с CE-B-W может НЕ пройти:** обратный маршрут к пересекающемуся `10.100.1.0/24` со стороны CUST_A уходит в CE-A-W1, и это не опровергает route leak. Ошибка должна быть устранена:

```text
conf t
ip vrf CUST_B
 no route-target import 65000:100
end
```

**Ограничение:** overlapped `10.100.1.0/24`/`10.100.3.0/24` неудобны для доказательства утечки: BGP может выбрать уже существующий маршрут своей VPN. Для подтверждения используйте именно A-only `10.100.4.0/24` или `10.100.2.0/24`.

---

### Контрольная карточка диагностики

Для каждой аварии фиксировать: `time initiated`, `expected`, `observed`, `OSPF status`, `LDP state`, `BGP VPNv4 state`, `VRF route`, `CE test`, `root cause`, `rollback`, `time recovered`. Ни одно значение времени восстановления не задано заранее: его следует измерять в вашей виртуальной среде.
