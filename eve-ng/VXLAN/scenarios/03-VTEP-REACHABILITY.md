# 03 — VTEP Loopback недоступен при здоровом BGP

**Этап:** 01  
**Задача:** воспроизвести характерный overlay blackhole при работающем BGP EVPN.

> Только изолированная лаборатория EVE-NG. Изменения применяются вручную к тестовым узлам. Команды не выполнять на рабочих сетевых устройствах. Конфигурации NX-OSv 9.3(x) и реальное поведение требуют проверки на образе.

## Baseline: докажи, что всё работает до сбоя

CLIENT-A → APP-C (VNI10020) и DB-B → DB-C (VNI10030) работают. На LEAF-01: `show ip route 10.254.0.23`, `show bgp l2vpn evpn summary`.

Перед изменением сохрани вывод `show running-config`, таблицы маршрутизации и результат теста. Фиксируй время и симптом, а не только успешность ping.

## Внести неисправность

На **LEAF-03** убрать Lo1 (VTEP) из OSPF, оставив Lo0/BGP:
```nxos
configure terminal
interface loopback1
 no ip router ospf UNDERLAY area 0.0.0.0
end
```

## Найти причину — control plane и data plane

- LEAF-01: `show ip route 10.254.0.23` — через некоторое время маршрут к VTEP может исчезнуть; `ping 10.254.0.23 source 10.254.0.21` не проходит.
- При этом `show bgp l2vpn evpn summary` к Lo0 RR остаётся Established; на LEAF-01 могут сохраняться Type-2/3 от LEAF-03.
- `show nve peers` и packet capture UDP/4789 помогут локализовать forwarding failure. BGP не обязан немедленно удалить MAC.
- Не считать проверкой только MAC-table: MAC/route могут быть stale.

## Откат

На LEAF-03:
```nxos
configure terminal
interface loopback1
 ip router ospf UNDERLAY area 0.0.0.0
end
```
Дождаться конвергенции OSPF и перепроверить data plane.

## Что объяснить в отчёте

Почему BGP к Loopback0 работает, когда VXLAN Loopback1 недоступен? Как отличить это от ошибки RT?

После отката обязательно повторить исходные проверки. Фиксировать **expected / observed / root cause / rollback / recovered** и приложить отдельные выводы команд до и после.
