## Исправление импорта и вариант без Linux-образа (2026-11-09)

В исходных `.unl` не было встроенных startup-config; в обновлённых файлах используется `<objects><configs>` (base64) и `config="1"`. Подробная инструкция: [STARTUP-CONFIG-REPAIR.md](docs/STARTUP-CONFIG-REPAIR.md).

- `VXLAN-FABRIC-5N-6H.unl` — embedded EVPN L2 configs.
- `VXLAN-FABRIC-MULTITENANT-NOFW.unl` — multi-VRF без Linux firewall (подходит для проверки Fabric/VRF, **не** даёт меж-VRF транзит).
- `VXLAN-FABRIC-MULTITENANT-IOSV-FW.unl` — multi-VRF с Cisco IOSv ACL router вместо Linux firewall, конфигурация встроена, **не stateful**. Требуется установленный образ IOSv.
- `VXLAN-FABRIC-MULTITENANT-FW.unl` — исходный сценарий c Debian/nftables; требует установленного QEMU образа `linux-vxlan-debian12` и ручной настройки Linux.

Отказ открытия лаборатории без текста ошибки EVE-NG не диагностирован. Наличие отсутствующего образа — возможная проблема, но не подтверждённая причина отказа UI.

# VXLAN EVPN Leaf–Spine — повторение старых лабораторий в EVE-NG CE

**Версия пакета:** 2026-10-26 · **платформа:** Cisco Nexus 9000v (ориентир 9.3.9) · **статус:** артефакты сгенерированы и статически проверены, **запуск в EVE-NG и проверка CLI на реальных образах не производились**.

Это продвинутая замена предыдущей лаборатории с двумя VTEP. Основана на архитектуре `https://github.com/thleontev/netlabs/tree/main/gns3/VXLAN`, содержит 5 коммутаторов, 6 VPCS, 2 независимых spine, 3 leaf. Мультитенантный вариант добавляет Debian firewall.

## Что было раньше

| Старый проект | Фактическое содержимое | Как отражено здесь |
|---|---|---|
| VXLAN Topology 2 (F&L) | 2 Spine + 3 Leaf; OSPF; PIM-SM; VNI 10010/10020/10030, группы 224.1.1.10/20/30; NX-OS Titanium 7.3 | Отдельная сравнительная работа в `docs/legacy-multicast.md`, без включения PIM в основной сценарий |
| VXLAN Topology 2_1 (F&L BIDIR) | Аналогичный underlay, PIM BIDIR с `ip pim rp-address ... bidir` | Разбор условий поддержки RP и диагностики |
| VXLAN Topology 3_1 (EVPN) | Nexus 9.3.1, BGP RR на Spine, EVPN, anycast gateway, tenant L3VNI | Стадии 01 и 02 |
| VXLAN Topology 3_3 (Multitenancy) | Отдельные VRF Clients, Web-Servers, DMZ, L3VNI; ASAv между VRF | Стадия 03: два VRF + Linux nftables firewall вместо лицензируемой ASAv |

**Принцип обновления:** старая multicast BUM-модель полезна для понимания VXLAN F&L. В новом основном сценарии L2 VNI используют `ingress-replication protocol bgp`: BGP EVPN рассылает список VTEP, так что PIM underlay не нужен. В обоих случаях overlay VXLAN несёт UDP/4789.

## Требования и возможные ограничения

- EVE-NG Community Edition с рабочим KVM/nested virtualization; 5 Nexus 9000v требуют около **40 GiB RAM только на сами гостевые узлы** (по 8 GiB), рекомендован хост с **64 GiB+**, достаточными физическими CPU-ядрами и диском.
- Легально полученный образ Cisco Nexus 9300v NX-OS 9.3.9. Готовый образ не вложен. EVE имя образа по умолчанию `nxosv9k-9300v-9.3.9`; в каталоге обычно должен лежать `sataa.qcow2` (проверить официальную HowTo под свою версию EVE).
- В EVE-NG есть VPCS по умолчанию; он используется для шести конечных хостов. Для второй .unl нужен дополнительно Debian QEMU образ `linux-vxlan-debian12` (или замена через скрипт).
- Настройки `ethernet`, `ram`, `template`, отображение `mgmt0/Ethernet1/x`, а также поддержка отдельных команд зависят от конкретного образа NX-OS и EVE. Проверить в консоли перед вводом. **Не считать .unl гарантированно запускаемым на иной версии без теста.**
- Ни один стенд не подключен к продуктивной домашней/серверной сети; управление/Cloud не добавлены в .unl во избежание случайного bridging.

Официальная инструкция EVE: https://www.eve-ng.net/index.php/documentation/howtos/howto-add-cisco-nexus-9000v-switch/ . Справочник Cisco для EVPN 9.3: https://www.cisco.com/c/en/us/td/docs/switches/datacenter/nexus9000/sw/93x/vxlan/configuration/guide/b-cisco-nexus-9000-series-nx-os-vxlan-configuration-guide-93x/b-cisco-nexus-9000-series-nx-os-vxlan-configuration-guide-93x_chapter_0101.html .

## Файлы

```
VXLAN-FABRIC-5N-6H.unl                 # Основная топология, 5 Nexus + 6 VPCS
VXLAN-FABRIC-MULTITENANT-FW.unl       # Топология + Debian firewall
configs/00-underlay/{SPINE,LEAF}*.cfg
configs/01-evpn-l2/{SPINE,LEAF}*.cfg
configs/02-symmetric-irb/{SPINE,LEAF}*.cfg
configs/03-multitenancy-fw/{SPINE,LEAF}*.cfg
configs/0{1,2,3}-*/VPCS-commands.txt
scripts/fw-setup.sh                   # Linux FW: маршрутизация + nftables
scripts/retarget_image.py             # Подмена имен QEMU образов в UNL
scripts/check_artifacts.py            # Статические тесты, НЕ runtime verification
docs/workbook.md                      # 4 этапа + гипотезы/критерии/проверки
docs/legacy-multicast.md             # Почему PIM-SM/BIDIR отличаются от BGP IR
```

## Схема L3 underlay и L2 access

```
                SPINE-01 (RR)              SPINE-02 (RR)
                 10.255.0.11               10.255.0.12
                 /     |   \               /   |     \
                /      |    \             /    |      \
               /       |     \           /     |       \
           LEAF-01   LEAF-02   LEAF-03  (каждый LEAF к обоим SPINE)
          .21 / VTEP .21  .22 / VTEP .22  .23 / VTEP .23
         CLIENT-A/APP-A   CLIENT-B/DB-B    APP-C/DB-C
```

Шесть *разных* bridge-network на L3 линках, шесть *разных* L2-access сетей. Никаких физических соединений leaf-to-leaf: взаимосвязь только через IP underlay, UDP/4789 и EVPN.

| Link | Leaf port | Leaf IP | Spine port | Spine IP |
|---|---|---|---|---|
| LEAF-01 ↔ SPINE-01 | E1/1 | 10.0.11.0/31 | E1/1 | 10.0.11.1/31 |
| LEAF-02 ↔ SPINE-01 | E1/1 | 10.0.12.0/31 | E1/2 | 10.0.12.1/31 |
| LEAF-03 ↔ SPINE-01 | E1/1 | 10.0.13.0/31 | E1/3 | 10.0.13.1/31 |
| LEAF-01 ↔ SPINE-02 | E1/2 | 10.0.21.0/31 | E1/1 | 10.0.21.1/31 |
| LEAF-02 ↔ SPINE-02 | E1/2 | 10.0.22.0/31 | E1/2 | 10.0.22.1/31 |
| LEAF-03 ↔ SPINE-02 | E1/2 | 10.0.23.0/31 | E1/3 | 10.0.23.1/31 |

| Node | Router ID / Lo0 | VTEP Lo1 |
|---|---|---|
| SPINE-01 | 10.255.0.11/32 | — |
| SPINE-02 | 10.255.0.12/32 | — |
| LEAF-01 | 10.255.0.21/32 | 10.254.0.21/32 |
| LEAF-02 | 10.255.0.22/32 | 10.254.0.22/32 |
| LEAF-03 | 10.255.0.23/32 | 10.254.0.23/32 |

| Host | Leaf access interface | VLAN/L2VNI | Address | Gateway stages 02–03 |
|---|---|---|---|---|
| CLIENT-A | LEAF-01 E1/3 | VLAN10 / 10010 | 192.168.10.11/24 | 192.168.10.1 |
| CLIENT-B | LEAF-02 E1/3 | VLAN10 / 10010 | 192.168.10.12/24 | 192.168.10.1 |
| APP-A | LEAF-01 E1/4 | VLAN20 / 10020 | 192.168.20.11/24 | 192.168.20.1 |
| APP-C | LEAF-03 E1/3 | VLAN20 / 10020 | 192.168.20.13/24 | 192.168.20.1 |
| DB-B | LEAF-02 E1/4 | VLAN30 / 10030 | 192.168.30.12/24 | 192.168.30.1 |
| DB-C | LEAF-03 E1/4 | VLAN30 / 10030 | 192.168.30.13/24 | 192.168.30.1 |

> L2VNI: 10010 / 10020 / 10030. Stage02: VRF TENANT1 / L3VNI 50001. На Leaf создаются только VLAN с локально подключёнными хостами: L1=10,20; L2=10,30; L3=20,30 (так гарантируется проверка L3VNI при трафике CLIENT-A→DB-C). Stage03: CLIENTS / L3VNI 50110, APPS / L3VNI 50220. `VLAN110` и `VLAN220` — локальные VLAN для L3VNI, не access VLAN. Underlay AS: 65000.

## EVE-NG Community Edition — импорт

1. Убедиться, что образ присутствует: `ls /opt/unetlab/addons/qemu/ | grep nxosv9k`.
2. Если имя отличается, на своём компьютере выполнить `python3 scripts/retarget_image.py VXLAN-FABRIC-5N-6H.unl --nxos <real-eve-folder-name>`. Для FW топологии дополнительно `--linux <image-folder>`.
3. Передать `.unl` на стенд (ранее использованный адрес сервера: `192.168.0.100`, проверить, что он всё ещё актуален):

   ```powershell
   scp .\VXLAN-FABRIC-5N-6H.unl root@192.168.0.100:/opt/unetlab/labs/
   ```

4. На EVE выполнить `/opt/unetlab/wrappers/unl_wrapper -a fixpermissions`.
5. Открыть лабораторию в веб-интерфейсе, проверить, что каждый NX-OS port `Ethernet1/x` соответствует схеме, при необходимости поправить номера линков. Если EVE запрашивает создание/замену образов, это надо сделать до запуска.
6. Запустить SPINE-01/02 и LEAF-01/02/03. После первого запуска пройти мастер начальной конфигурации NX-OS и сохранить пароль. **Конфигурации не применяются автоматически в EVE CE**: на каждой ноде выполнить `configure terminal`, затем вставить содержимое соответствующего CFG (строки, начинающиеся `!`, можно оставлять). `copy run start` сохранить после проверки.
7. Для перехода к следующему этапу рекомендуется **сначала откатить узлы к исходному состоянию / очистить lab instance**, а затем применять полный файл нового этапа. Если требуется не терять running-config, самостоятельно применить diff конфигураций и удалить устаревшие VRF/VNI — простое копирование полного конфига поверх старого может оставить лишние элементы. Backup конфигурации обязателен.
8. В VPCS отдельно применить команды `configs/<stage>/VPCS-commands.txt`, поскольку хосты не получают IP из .unl.

**Проверка сетевых портов** на NX-OS: `show interface brief`, `show interface status`, `show ip interface brief`. С учётом платформы `mgmt0` может занимать отдельную EVE-NG NIC, а E1/1 — следующий порт. Если отображаемые в редакторе EVE номера отличаются, скорректировать подключения, а не IP-план вслепую.

## Этапы

| Stage | Цель | Включено в cfg | Проверка |
|---|---|---|---|
| **00** Underlay | OSPF, /31 линк, /32 Lo, ECMP, отказ spine | `configs/00-underlay` | 2 OSPF соседства у leaf / 3 у spine, все VTEP lo достижимы |
| **01** VXLAN EVPN L2 | VLAN/VNI; EVPN route types 2,3; BUM ingress replication | `configs/01-evpn-l2` | CLIENT-A ↔ CLIENT-B, APP-A ↔ APP-C, DB-B ↔ DB-C проходят; разные VLAN не маршрутизируются |
| **02** Symmetric IRB | VRF TENANT1; L3VNI 50001; Anycast GW | `configs/02-symmetric-irb` | CLIENT-A ↔ DB-C через L3VNI, поскольку у LEAF-01 нет VLAN30 |
| **03** Multitenancy / FW | VRF CLIENTS+APPS; два L3VNI, отдельная зона фаервола | `configs/03-multitenancy-fw` + Linux script | внутри VRF пинг; между VRF политики FW решают доступ |

## Важная последовательность проверки

1. OSPF: `show ip ospf neighbors`, `show ip route 10.254.0.22`, `ping 10.254.0.23 source 10.254.0.21` (соответствующий Leaf).
2. BGP: `show bgp l2vpn evpn summary` — оба Spine как RR должны быть Established.
3. Overlay: `show nve peers`, `show nve vni`, `show bgp l2vpn evpn`, `show l2route evpn mac all`.
4. После ping из VPCS: Type-2 для MAC/IP, Type-3 IMET для BUM, Type-5 для сети клиента при включённом `advertise l2vpn evpn` + redistribution (могут зависеть от версии NX-OS).
5. L3: `show ip route vrf TENANT1`, `show nve vrf`, `show forwarding ipv4 route vrf TENANT1` (синтаксис последнего зависит от версии), `show ip arp vrf TENANT1`.
6. Failover: в EVE вручную остановить SPINE-01, убедиться, что OSPF и BGP переключаются, а hosts получают связь через SPINE-02. После восстановления проверить снова.

Выполнение предыдущего шага обязательно до следующего. В `docs/workbook.md` есть учебные вопросы и шаги отказных сценариев.

## Переход 03: firewall

FW подключён **только к LEAF-02**, отдельными routed интерфейсами в VRF CLIENTS и VRF APPS. В `.unl` Debian использует `interface id=1` и `id=2`; названия гостевых интерфейсов Debian могут быть `ens4`/`ens5` вместо `eth1`/`eth2`. Параметризовать так:

```bash
sudo CLIENT_IF=ens4 APPS_IF=ens5 bash scripts/fw-setup.sh
```

Заменить на реально найденные `ip -br link` интерфейсы. Linux firewall по умолчанию разрешает **только ICMP от CLIENTS к APPS** и установленный ответный трафик; прочие новые межзонные соединения запрещает. Это нужно для безопасного учебного теста, **не конфигурация production firewall**. На LEAF-02 статики в соответствующих VRF имеют `tag 101`, на маршруты применяется BGP route-map `RM_FIREWALL`. Диагностика: `show ip route vrf CLIENTS`, `show ip route vrf APPS`, `show bgp l2vpn evpn`, `nft list ruleset`, `tcpdump`.

## Критерии готовности

- Можешь объяснить, зачем нужны Lo0 (BGP update-source / router-id) и Lo1 (VTEP), зачем Spine RR и почему Spine **не** VTEP.
- Можешь по `show bgp l2vpn evpn` найти Type-2/3/5 и определить, у какого VTEP находится хост.
- Можешь за 10 минут локализовать отказ подмножества hosts между underlay, BGP, RT/VNI, шлюзом и FW.
- Можешь объяснить, почему без firewall VRF CLIENTS и VRF APPS изолированы и почему объединять их прямым RT-import нельзя, если нужна централизованная инспекция.
- Можешь сравнить multicast Flood & Learn старой лаборатории и ingress replication/EVPN.

## Границы проверок

Скрипт `scripts/check_artifacts.py` проверяет XML, отсутствие конфликтов interface/network id, наличие 6 underlay и 6 access связей, обязательные BGP/OSPF/VNI/VRF секции и непротиворечивость IP-плана. Он **не** может обнаружить недоступные NX-OSv команды, несовместимый image, проблемы boot/KVM или runtime reachability. Тесты выполнены локально, но работу конкретного EVE-хоста надо проверить вручную.

## Дополнительные практические сценарии (break/fix)

В отличие от четырёх последовательных стадий `configs/`, сценарии — это **независимые fault-injection упражнения** на уже запущенной соответствующей стадии. Формат воспроизводит подход из [DDOS](../DDOS/scenarios/) и [MPLS](../MPLS/scenarios/FAULTS.md): исходная проверка → ввод одной неисправности → control-plane/data-plane evidence → точный rollback.

- [Каталог 13 сценариев](scenarios/README.md) — от baseline/ECMP до VTEP blackhole, RT, Type-5, межсетевого экрана и PMTUD.
- [Диагностическая карта](docs/SCENARIO-DIAGNOSTICS.md) — разделение отказов по уровням, команды и шаблон отчёта.

Эти материалы **не добавляют новых устройств** в `.unl`; сценарий MTU требует заменить часть VPCS на Linux при тестировании DF. Сценарии подготовлены по CLI существующих конфигураций, **фактический запуск в EVE-NG/на Nexus 9000v не подтверждён**.
