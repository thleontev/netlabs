# 05 — Потеря ingress replication для одного VNI

**Этап:** 01  
**Задача:** отделить BUM flood list/ARP discovery от известного unicast MAC forwarding.

> Только изолированная лаборатория EVE-NG. Изменения применяются вручную к тестовым узлам. Команды не выполнять на рабочих сетевых устройствах. Конфигурации NX-OSv 9.3(x) и реальное поведение требуют проверки на образе.

## Baseline: докажи, что всё работает до сбоя

На LEAF-03: `show running-config interface nve1`, `show nve vni`, `show bgp l2vpn evpn`. APP-A↔APP-C и DB-B↔DB-C проверены.

Перед изменением сохрани вывод `show running-config`, таблицы маршрутизации и результат теста. Фиксируй время и симптом, а не только успешность ping.

## Внести неисправность

На **LEAF-03**:
```nxos
configure terminal
interface nve1
 member vni 10020
  no ingress-replication protocol bgp
end
```

## Найти причину — control plane и data plane

- Сравнить `show nve vni`, `show nve peers`, Type-3 IMET и flood list (доступные show зависят от NX-OS).
- С новым ARP discovery APP-C→APP-A и APP-A→APP-C могут перестать работать/стать асимметричными; старые ARP/MAC и существующий unicast могут продолжать проходить.
- VNI10030 не менялся: DB-B↔DB-C должен оставаться рабочим.
- Capture на uplink: ARP как внутренняя часть VXLAN UDP/4789. Для воспроизводимости перезапусти лабораторные VPCS или дождись ARP expiry, зафиксируй что было очищено.

## Откат

На LEAF-03:
```nxos
configure terminal
interface nve1
 member vni 10020
  ingress-replication protocol bgp
end
```

## Что объяснить в отчёте

Чем IMET Type-3 отличается от MAC/IP Type-2? Почему нельзя судить о состоянии BUM по непрерывному ping?

После отката обязательно повторить исходные проверки. Фиксировать **expected / observed / root cause / rollback / recovered** и приложить отдельные выводы команд до и после.
