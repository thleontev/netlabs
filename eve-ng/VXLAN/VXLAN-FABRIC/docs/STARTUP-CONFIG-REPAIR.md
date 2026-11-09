# VXLAN — восстановление загрузки EVE-NG CE (2026-11-09)

Первоначальные VXLAN .unl были без встроенного startup-config. В исправленных .unl содержатся `<objects><configs>` с base64 для Cisco Nexus и VPCS; их узлы используют `config="1"`. Настоящий запуск на пользовательском EVE-NG CE не подтверждён.

## Доступные варианты

- `VXLAN-FABRIC-5N-6H.unl` — 5 NXOS + 6 VPCS, EVPN L2, startup-config.
- `VXLAN-FABRIC-MULTITENANT-FW.unl` — 5 NXOS + 6 VPCS + Linux `linux-vxlan-debian12`; **требует существования этого образа**, иначе Linux узел не запустится. Фактическая причина сбоя открытия неизвестна.
- `VXLAN-FABRIC-MULTITENANT-NOFW.unl` — 5 NXOS + 6 VPCS, нет дополнительного Linux узла; inter-VRF forwarding через FW не работает.
- `VXLAN-FABRIC-MULTITENANT-IOSV-FW.unl` — 5 NXOS + 6 VPCS + IOSv. Это вариант с ACL-роутером вместо Linux/nftables; **НЕ stateful firewall**. В IOSv настроено разрешение ICMP CLIENTS→APPS и echo-reply обратно, а остальные маршрутизируемые соединения блокируются ACL. Оба линка LEAF-02 к FW сохранены.

## Зависимости IOSv-версии

```bash
ls -1 /opt/unetlab/addons/qemu/ | grep -E '^(nxosv9k|vios)-'
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
```

Имена образов в `.unl`: `nxosv9k-9300v-9.3.9` и `vios-adventerprisek9-m.SPA.159-3.M6`. При отличии папок изменить атрибут `image` на точное имя существующей папки. Новую лабораторию скопировать в `/opt/unetlab/labs/VXLAN/`, в Web UI открыть её отдельно. Встроенные startup configs иногда требуют **Wipe** после активации (Wipe удаляет данные node; сначала сохранить нужную конфигурацию). Linux-версия требует ручной настройки Linux через `scripts/fw-setup.sh`.

## Схема FW-IOSV

- LEAF-02 Ethernet1/5, VRF CLIENTS `172.31.10.1/30` ↔ FW-IOSV `GigabitEthernet0/0`, `172.31.10.2/30`
- LEAF-02 Ethernet1/6, VRF APPS `172.31.20.1/30` ↔ FW-IOSV `GigabitEthernet0/1`, `172.31.20.2/30`
- IOSv routes: `192.168.10.0/24` via CLIENTS, `192.168.20.0/24` / `192.168.30.0/24` via APPS
- Tests: `show ip route vrf CLIENTS` / `show ip route vrf APPS` on LEAF-02, `show ip interface brief`, `show access-lists` on FW-IOSV

Если EVE не **открывает** сам файл, а не просто не запускает Linux, нужен текст PHP/HTML ошибки (или снимок экрана). Наличие отсутствующего Linux image само по себе не подтверждает корневую причину невозможности открытия.

Состояние: XML, 12 узлов, 14 мостов по два endpoint, 12 декодируемых встроенных startup-config, FW interface ids 0/1, IP адреса и линки проверены статически. Не проверялось загрузкой в EVE-NG.
