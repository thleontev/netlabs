# 09 — Статический маршрут есть в VRF, но Type-5 не экспортируется

**Этап:** 03  
**Задача:** разделить локальную статическую маршрутизацию LEAF-02 и распространение IP-префиксов через EVPN.

> Только изолированная лаборатория EVE-NG. Изменения применяются вручную к тестовым узлам. Команды не выполнять на рабочих сетевых устройствах. Конфигурации NX-OSv 9.3(x) и реальное поведение требуют проверки на образе.

## Baseline: докажи, что всё работает до сбоя

На LEAF-02: `show ip route vrf CLIENTS 192.168.20.0/24` показывает next-hop 172.31.10.2; на LEAF-01 в VRF CLIENTS есть соответствующий удалённый путь. CLIENT-A→APP-C разрешён firewall.

Перед изменением сохрани вывод `show running-config`, таблицы маршрутизации и результат теста. Фиксируй время и симптом, а не только успешность ping.

## Внести неисправность

На **LEAF-02**, в BGP VRF CLIENTS:
```nxos
configure terminal
router bgp 65000
 vrf CLIENTS
  address-family ipv4 unicast
   no redistribute static route-map RM_FIREWALL
end
```

## Найти причину — control plane и data plane

- LEAF-02: `show ip route vrf CLIENTS 192.168.20.0/24` всё ещё видит static; BGP EVPN Type-5 для этого импорта может исчезнуть после convergence.
- LEAF-01: `show ip route vrf CLIENTS 192.168.20.0/24`, `show bgp l2vpn evpn` — может пропасть удалённый путь к APPS via FW.
- Внутри CLIENTS L2VNI 10010 по-прежнему должен работать.
- Если на LEAF-01 маршрут остаётся, проверить альтернативный источник Type-5 / stale route; не выдавать ping failure без анализа RIB.

## Откат

На LEAF-02:
```nxos
configure terminal
router bgp 65000
 vrf CLIENTS
  address-family ipv4 unicast
   redistribute static route-map RM_FIREWALL
end
```

## Что объяснить в отчёте

Как доказать, что потерян именно экспорт Type-5, а не доступность next-hop 172.31.10.2?

После отката обязательно повторить исходные проверки. Фиксировать **expected / observed / root cause / rollback / recovered** и приложить отдельные выводы команд до и после.
