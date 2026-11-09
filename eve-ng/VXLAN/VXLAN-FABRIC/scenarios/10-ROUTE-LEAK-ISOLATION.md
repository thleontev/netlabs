# 10 — Ошибочный импорт APPS Route Target в CLIENTS

**Этап:** 03  
**Задача:** показать policy leak и отличие самого факта импорта маршрута от реального firewall bypass.

> Только изолированная лаборатория EVE-NG. Изменения применяются вручную к тестовым узлам. Команды не выполнять на рабочих сетевых устройствах. Конфигурации NX-OSv 9.3(x) и реальное поведение требуют проверки на образе.

## Baseline: докажи, что всё работает до сбоя

До вмешательства: LEAF-01 `show ip route vrf CLIENTS`, `show ip route vrf APPS`, `show bgp l2vpn evpn`. Сверь у Type-5 APPS реальный extended community RT (в эталоне ожидается производный от L3VNI 50220; уточнить на своём образе).

Перед изменением сохрани вывод `show running-config`, таблицы маршрутизации и результат теста. Фиксируй время и симптом, а не только успешность ping.

## Внести неисправность

На **LEAF-01** вводим заведомо неверный cross-VRF import, **только если предварительно подтвержден RT APPS**:
```nxos
configure terminal
vrf context CLIENTS
 address-family ipv4 unicast
  route-target import 65000:50220
  route-target import 65000:50220 evpn
end
```
Если фактический RT отличается — не выполняй заготовку буквально: адаптируй только после проверки `show bgp l2vpn evpn`.

## Найти причину — control plane и data plane

- `show ip route vrf CLIENTS` и BGP EVPN: искать APPS-only префиксы (например 192.168.20.0/24) с импортом по новому RT.
- **Наличие чужого префикса уже доказывает policy leak**, даже если ICMP не проходит (L3VNI resolution, firewall, next-hop и обратный маршрут могут препятствовать).
- Поскольку в Stage03 LEAF-02 **уже законно экспортирует** 192.168.20.0/24 через FW в CLIENTS, этот префикс может быть неуникальным доказательством. Для чистого теста необходимо выделить дополнительный APPS-only prefix с единственным источником и подтвердить его origin, либо сравнить BGP paths и RT.
- Не трактовать тест как автоматический обход firewall; для его подтверждения нужен фактический packet path и stateful policy.

## Откат

На LEAF-01:
```nxos
configure terminal
vrf context CLIENTS
 address-family ipv4 unicast
  no route-target import 65000:50220
  no route-target import 65000:50220 evpn
end
```
Проверить удаление чужого RT и маршрута.

## Что объяснить в отчёте

В чём угроза неверного RT для мультиарендности? Почему ping может быть ложным отрицательным тестом policy leak?

После отката обязательно повторить исходные проверки. Фиксировать **expected / observed / root cause / rollback / recovered** и приложить отдельные выводы команд до и после.
