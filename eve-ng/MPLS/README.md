# MPLS Service Provider Advanced — EVE-NG CE

**Version 2.0 · 2026-10-27 · standalone updated lab**

Не элементарная цепочка из P/PE: **16 маршрутизаторов, 23 физических линка, 2 Route Reflector, 4 PE, 4 P, 6 CE, 2 VRF, dual-homed CE, перекрывающаяся клиентская IPv4-адресация, 7 аварийных сценариев**.

**Статус**: выполнена *офлайн-валидация*, но EVE-NG/IOSv здесь не запускались. `.unl` не содержит образов и не применяет конфигурации автоматически. Корректность команд на вашей конкретной версии IOSv проверяется запуском в EVE-NG.

## Файлы

| Файл | Назначение |
|---|---|
| `MPLS-SP-Advanced.unl` | Топология EVE-NG Community Edition (16 QEMU vIOS nodes, 23 bridge links) |
| `docs/topology.svg` / `.png` | Общая схема: два основных направления, CE, P, PE, RR |
| `docs/link-plan.svg` / `.png` | Подробный план всех интерфейсов, подсетей и OSPF-cost |
| `docs/LINKS.csv` | Точная таблица `Gi0/x`, IP каждого конца линка, OSPF-cost, VRF |
| `docs/topology.json` | Машиночитаемый источник сетевой модели |
| `configs/00-underlay/*.cfg` | 16 начальных конфигураций: адреса, OSPF в core, только L3 IP |
| `configs/01-ldp/*.cfg` | 16 конфигураций: OSPF + LDP/MPLS на транзитных P/PE интерфейсах |
| `configs/02-l3vpn/*.cfg` | 16 полных конфигураций: RR/VPNv4, VRF, RD/RT, eBGP PE–CE, local-pref |
| `docs/EXERCISES.md` | Этапы лаборатории и наблюдаемые критерии выполнения |
| `docs/DIAGNOSTICS.md` | Команды по уровням control plane/data plane |
| `docs/EXTENSIONS.md` | Следующие отдельные модули (Inter-AS, TE, L2VPN, EVPN/SR); пока не входят в рабочую `.unl` |
| `scenarios/FAULTS.md` | Семь break/fix-сценариев с конфигурациями ввода/отката |
| `tools/build_lab.py` | Детерминированная генерация `.unl`, CLI и CSV/JSON (stdlib) |
| `tools/render_diagrams.py` | Генерация SVG/PNG из модели (`svgwrite`, `cairosvg`) |
| `tools/validate_lab.py` | Офлайн-проверка структуры, IP-плана, связности и файлов |
| `tools/rewrite_image.py` | Замена имени QEMU image в `.unl`, без перестройки топологии |

## Архитектура

**AS провайдера** `65000`, OSPF process `100`, area `0`, LDP по интерфейсам P/PE. 

**Control plane:** PE-W1/W2/E1/E2 устанавливают iBGP VPNv4 к RR1 (`10.255.0.21`) и RR2 (`10.255.0.22`). RR подключены *только к одному P* каждый, чтобы не стать транзитными узлами без MPLS. Они обмениваются VPNv4 UPDATE и отражают маршруты, не являясь MPLS data plane. RR между собой iBGP *не обязателен*: все PE подключены к обоим RR.

**Data plane:** PE-W1 → P1 → P3 → PE-E1 — минимальная стоимость IGP (10+10+10=30). Второй основной тракт: PE-W2 → P2 → P4 → PE-E2. Дополнительные перекрёстные соединения позволяют перестроение SPF при обрыве магистрали. **OSPF может выбрать ECMP** при отдельных авариях, так как есть равностоимостные обходы.

**Клиенты:**

| VRF | RT import/export | CE площадки | LAN-префиксы |
|---|---|---|---|
| CUST_A | 65000:100 | CE-A-W1, CE-A-W2, CE-A-E1, CE-A-E2 | 10.100.1.0/24, .2.0/24, .3.0/24, .4.0/24 |
| CUST_B | 65000:200 | CE-B-W, CE-B-E | 10.100.1.0/24, 10.100.3.0/24 |

Аналогичные подсети у **разных** клиентов не конфликтуют: CE-B-W и CE-A-W1 могут иметь один и тот же адрес `10.100.1.1` в разных VPN. RD уникален **для каждого PE/VRF**, но **RT общий внутри одного сервиса**.

CE-A-W1 дважды подключён к разным PE: Gi0/0 → PE-W1 (`10.11.1.0/30`), Gi0/1 → PE-W2 (`10.11.2.0/30`). На PE-W1 входящим маршрутам от CE-A-W1 задаётся `local-preference 200`, на PE-W2 — стандартное 100. У CE-A-W1 `weight 500` для маршрутов от PE-W1. Поэтому желаемое направление до обрыва — через PE-W1; после аварии должен работать PE-W2. Это **лабораторный** способ приоритизации, а не универсальная политика для оператора.

### Ограничения на оборудовании

Cisco CML документирует для IOSv поддержку **MPLS, MPLS L2VPN/L3VPN, MPLS TE**, но **BFD и VPLS не поддерживаются**. В эту версию НЕ включены VPLS, BFD, Segment Routing и EVPN-MPLS: потребуются отдельные образы/лабы. IOS XR конфигурации старых GNS3-работ нельзя применять к IOSv без адаптации. Реализован LDP, а не RSVP-TE или SR-MPLS.

- Cisco IOSv documentation: <https://developer.cisco.com/docs/modeling-labs/2-2/iosv/>
- Прежние MPLS исследования: <https://github.com/thleontev/netlabs/tree/main/gns3/MPLS>
- Прежние VXLAN исследования: <https://github.com/thleontev/netlabs/tree/main/gns3/VXLAN>

## Запуск EVE-NG CE

**Ресурсы:** 8 × P/PE с 1 GB, 2 × RR с 768 MB, 6 × CE с 512 MB = **12.5 GB гостевой RAM**, без накладных расходов гипервизора и EVE-NG. Рекомендовано 20–24+ GB свободной RAM и достаточное CPU время на хосте. Для уменьшения нагрузки стартуйте узлы поэтапно.

**QEMU image:** по умолчанию `vios-adventerprisek9-m.SPA.159-3.M6`; Cisco IOSv образы **не распространяются** с этой лабораторией. Если каталог отличается, измените имя образа через EVE или:

```powershell
py tools/rewrite_image.py --image vios-НАЗВАНИЕ-ВАШЕЙ-ПАПКИ
```

Получится `MPLS-SP-Advanced-local.unl`. Сверьте с `ls -1 /opt/unetlab/addons/qemu/ | grep '^vios-'`. Для vIOS обычно требуется подготовленный `virtioa.qcow2`. Если используете иной шаблон или IOS-XR, **не подменяйте одно имя без изменения template/interface naming/config syntax**.

Выполните на локальном компьютере (пример IP EVE из предыдущей конфигурации; замените, если изменился):

```powershell
scp .\MPLS-SP-Advanced.unl root@192.168.0.100:/opt/unetlab/labs/
```

На EVE:

```bash
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
```

Затем откройте в web UI лабораторию и запустите устройства. Для загрузки CLI: открыть консоль соответствующего IOSv, вставить содержимое `configs/00-underlay/<device>.cfg` целиком. **Конфиги не стартовые EVE startup-config**; они содержат команды `enable`, `configure terminal`, `end`.

**Предупреждение о смене стадий:** `01-ldp` и `02-l3vpn` — *полные*, а не дифференциальные CLI файлы. Для воспроизводимого результата лучше сбросить узлы до пустого startup-config, после чего применить нужную фазу. При переходе с фазы 00/01 на 02 особенно важно убрать прежнюю глобальную конфигурацию PE–CE, поскольку IP интерфейса переносится во VRF (`ip vrf forwarding` сбрасывает IP). Система конфигурации не должна быть развернута в production.

## Чекпоинты

1. **IP**. `show ip ospf neighbor` на PE/W/P; `show ip route 10.255.0.3` на PE-W1.
2. **MPLS**. `show mpls ldp neighbor`, `show mpls forwarding-table`, `show mpls interfaces` на P и PE.
3. **VPNv4**. `show bgp vpnv4 unicast all summary` (на IOSv также распространён старый `show ip bgp vpnv4 all summary`), `show ip route vrf CUST_A`, `show ip bgp vpnv4 all labels`.
4. **Изоляция**. С CE-A-W1 `ping 10.100.4.1 source Loopback0`, с CE-B-W `ping 10.100.3.1 source Loopback0`; у A нет маршрута к B-сайтам, если их префиксы не входят в A — учтите, что `10.100.3.0/24` намеренно существует одновременно и у A, и у B.
5. **Аварии**. P1–P3 shutdown → SPF перестраивается, BGP VPNv4 должен сохраниться, клиентский трафик должен восстановиться через оставшиеся P; CE-A-W1 → PE-W1 shutdown → CE-A-W1 использует PE-W2.

Полный порядок работ: `docs/EXERCISES.md`. Инструкции break/fix: `scenarios/FAULTS.md`.

## Статическая проверка и ограничения

```bash
python3 tools/validate_lab.py
# PASS: 16 nodes, 23 links, 48 CLI configs, 8 distinct RD
```

Проверяются XML, точные номера интерфейсов, уникальность адресов, OSPF-cost, генерируемые конфигурации, RD, RT и наличие альтернативного пути в модели. Это **не имитирует работу Cisco IOSv**, не проверяет подлинное состояние BGP/LDP или фактический обмен пакетами. До эксплуатации в лаборатории EVE-NG необходимо проверить все 16 запущенных устройств.
