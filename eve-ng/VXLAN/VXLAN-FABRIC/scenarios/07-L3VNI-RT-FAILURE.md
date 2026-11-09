# 07 — L3VNI RT не импортирует удалённые префиксы

**Этап:** 02  
**Задача:** изолировать VRF/L3VNI маршруты от исправных L2VNI.

> Только изолированная лаборатория EVE-NG. Изменения применяются вручную к тестовым узлам. Команды не выполнять на рабочих сетевых устройствах. Конфигурации NX-OSv 9.3(x) и реальное поведение требуют проверки на образе.

## Baseline: докажи, что всё работает до сбоя

На LEAF-01: `show running-config vrf TENANT1`, `show ip route vrf TENANT1`; CLIENT-A → CLIENT-B и CLIENT-A → DB-C работают.

Перед изменением сохрани вывод `show running-config`, таблицы маршрутизации и результат теста. Фиксируй время и симптом, а не только успешность ping.

## Внести неисправность

На **LEAF-01** отключить стандартную авто-политику EVPN RT для IP-VRF (изменятся и import, и export):
```nxos
configure terminal
vrf context TENANT1
 address-family ipv4 unicast
  no route-target both auto evpn
end
```

## Найти причину — control plane и data plane

- На LEAF-01: `show bgp l2vpn evpn` и `show ip route vrf TENANT1`: сравнить Type-5/VRF префиксы, особенно 192.168.30.0/24 (локального VLAN30 нет).
- CLIENT-A→CLIENT-B (один L2VNI 10010) должен быть доступен при стабильном VTEP. CLIENT-A→DB-C (другой VNI) может перестать работать из-за отсутствия импортированного удалённого IP-префикса.
- Подтвердить `show nve vrf`, `show nve vni`; Type-2/3 на L2 могут сохраниться.
- Если после удаления RT маршруты не изменились, выяснить, какие именно EVPN route-type применяются данным образом; не считать тест автоматически успешным.

## Откат

На LEAF-01:
```nxos
configure terminal
vrf context TENANT1
 address-family ipv4 unicast
  route-target both auto evpn
end
```

## Что объяснить в отчёте

Чем L2VNI отличается от L3VNI при симметричном IRB? Почему удалённая сеть DB-C требует L3 route?

После отката обязательно повторить исходные проверки. Фиксировать **expected / observed / root cause / rollback / recovered** и приложить отдельные выводы команд до и после.
