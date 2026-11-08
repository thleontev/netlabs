# 02 — Отключение одного BGP EVPN RR-пира

**Этап:** 01  
**Задача:** проверить резервирование BGP control plane без падения L3 транспорта.

> Только изолированная лаборатория EVE-NG. Изменения применяются вручную к тестовым узлам. Команды не выполнять на рабочих сетевых устройствах. Конфигурации NX-OSv 9.3(x) и реальное поведение требуют проверки на образе.

## Baseline: докажи, что всё работает до сбоя

На LEAF-01: `show bgp l2vpn evpn summary` — два RR, `show ip route 10.255.0.11` — IP к RR есть. CLIENT-A → CLIENT-B работает.

Перед изменением сохрани вывод `show running-config`, таблицы маршрутизации и результат теста. Фиксируй время и симптом, а не только успешность ping.

## Внести неисправность

На **LEAF-01** (отключаем только EVPN BGP peer с SPINE-01):
```nxos
configure terminal
router bgp 65000
 neighbor 10.255.0.11
  shutdown
end
```
Если образ NX-OS отказывается принимать `shutdown` в этом submode — остановись, уточни `?`, не удаляй entire BGP process.

## Найти причину — control plane и data plane

- `show bgp l2vpn evpn summary`: peer 10.255.0.11 down/Idle (конкретное состояние зависит от версии); 10.255.0.12 остаётся Established.
- `show ip ospf neighbors` и `show ip route 10.255.0.11`: unchanged; IP до SPINE-01 **сохранился**.
- После повторного MAC-learning CLIENT-A↔CLIENT-B должен работать через второй RR, если тот сохранил Type-2/Type-3.
- `show bgp l2vpn evpn` и `show nve peers` могут отражать graceful-restart/stale routes — проверять по фактическому трафику.

## Откат

На LEAF-01:
```nxos
configure terminal
router bgp 65000
 neighbor 10.255.0.11
  no shutdown
end
```
Повторить `show bgp l2vpn evpn summary`.

## Что объяснить в отчёте

Может ли путь data plane сохраняться при потере BGP control plane? Что произойдёт при одновременной потере второго RR спустя время?

После отката обязательно повторить исходные проверки. Фиксировать **expected / observed / root cause / rollback / recovered** и приложить отдельные выводы команд до и после.
