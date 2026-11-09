# Диагностика — OSPF Multiarea

Команды ниже выполняются **в работающей EVE-NG**, а не являются уже полученными результатами. Поскольку в лаборатории смешаны IOSv и IOS XRv, синтаксис различается.

## Базовая проверка

| Объект проверки | IOSv (R5–R12) | IOS XRv (XR1–XR4) |
|---|---|---|
| IP-интерфейсы | `show ip interface brief` | `show ipv4 interface brief` |
| OSPF-соседства | `show ip ospf neighbor` | `show ospf neighbor` |
| OSPF-интерфейсы | `show ip ospf interface brief` | `show ospf interface brief` |
| LSDB | `show ip ospf database` | `show ospf database` |
| OSPF-маршруты | `show ip route ospf` | `show route ospf` |
| Все IPv4-маршруты | `show ip route` | `show route ipv4 unicast` |

## Ключевые контрольные точки

1. **Backbone area 0:** XR1, XR3, R6, R7, R8 — проверить состояние соседей и соответствие сетей/областей.
2. **Area 100:** XR1, XR2, XR3, XR4, R5 — проверить доступность Loopback из других областей.
3. **Virtual link:** на R6 и R10 выполнить `show ip ospf virtual-links`, затем проверить LSDB и межобластные маршруты. Virtual link идёт через area 200.
4. **Stub area 51:** на XR1 и R11 проверить область, соседство, default route и отсутствие запрещённых внешних LSA.
5. **NSSA area 300:** на R8 и R12 проверить параметры NSSA и поведение маршрутов после `redistribute connected subnets` на R12.
6. **EIGRP ↔ OSPF:** на R9 — `show ip eigrp neighbors` и `show ip route`; на XR2 — команды `show eigrp` и `show route` в поддерживаемом данной версией IOS XR синтаксисе. Проверить источники полученных маршрутов.

## Если соседство OSPF не устанавливается

Проверяйте последовательно: (1) интерфейсы и физические соединения по [топологии](topology.png), (2) IPv4-адреса и маски, (3) OSPF area/тип области, (4) Hello/Dead, (5) тип аутентификации и ключи, (6) MTU, (7) роль DR/BDR в общем L2-сегменте.

В этой лаборатории есть MD5 и key-chain, а на R6–R10 встречается `ip ospf dead-interval minimal hello-multiplier 4`. Не заменяйте параметры «на стандартные» при диагностике, если задача — сохранить исходную лабораторию.

### Изолированная диагностика

```text
show ip ospf neighbor
show ip ospf interface brief
show ip ospf database
show ip route ospf
show ip ospf virtual-links
```

Команды в блоке относятся к IOSv; для IOS XRv используйте соответствующие аналоги из таблицы выше.

[← Описание лаборатории](../README.md)
