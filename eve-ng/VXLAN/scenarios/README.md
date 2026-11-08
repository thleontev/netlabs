# VXLAN EVPN — практические сценарии

Адаптация подхода из [DDOS](../../DDOS/scenarios/) (отдельные проверяемые сценарии, AS-path/packet-path, отказ и rollback) и [MPLS](../../MPLS/scenarios/FAULTS.md) (break/fix, VRF, control plane vs data plane).

**Сначала** открыть [основной README](../README.md) и [workbook](../docs/workbook.md), подготовить EVE-NG, загрузить ПОЛНЫЙ конфиг соответствующей стадии на **чистую** конфигурацию Nexus, настроить VPCS; только затем выполнить сценарий. Ниже операции — **не патчи для переключения стадий**, а локальные инъекции отказов в конкретной стадии. Смену стадии делать через сброс lab instance / чистую загрузку, не вставлять полный конфиг поверх предыдущего без очистки.

| ID | Название | Stage | Главный проверяемый вывод |
|---|---|---|---|
| [00](00-BASELINE.md) | Базовые пути и границы | 00–03 | Карта OSPF/BGP/NVE/VRF; ожидаемые успешные и неуспешные тесты |
| [01](01-UPLINK-FAILOVER.md) | Потеря uplink | 00–01 | Failover через второй Spine |
| [02](02-RR-PEER-FAILURE.md) | Потеря одного BGP RR-пира | 01 | Control plane избыточен без изменения underlay |
| [03](03-VTEP-REACHABILITY.md) | VTEP Lo1 не объявлен в OSPF | 01 | EVPN Established не доказывает VXLAN forwarding |
| [04](04-L2-RT-MISMATCH.md) | Неверный L2 RT | 01 | Частичный отказ конкретного VNI |
| [05](05-BUM-REPLICATION.md) | Потеря BUM replication | 01 | Влияние Type-3/ARP flood list |
| [06](06-ANYCAST-SVI-OUTAGE.md) | Локальный Anycast SVI выключен | 02 | L2 и L3 отказ различаются |
| [07](07-L3VNI-RT-FAILURE.md) | Поломка L3VNI RT | 02 | Type-5/VRF в отличие от L2 Type-2 |
| [08](08-FIREWALL-PATH.md) | Firewall не маршрутизирует | 03 | Inter-VRF путь и проверка обратного трафика |
| [09](09-TYPE5-EXPORT.md) | Сломан экспорт статик через EVPN | 03 | Маршрут локально есть, удалённого Type-5 нет |
| [10](10-ROUTE-LEAK-ISOLATION.md) | Ошибочный cross-VRF RT import | 03 | Утечка маршрутов, не обязательно ping/bypass |
| [11](11-MTU-PMTUD.md) | MTU и PMTUD VXLAN | 02, optional Linux | Увеличение пакета на VXLAN encapsulation |
| [12](12-OSPF-COST-ECMP.md) | Смещение OSPF cost | 00–01 | Восстановление пути без обрыва BGP |

## Методика

1. **Предсказание:** что должно остаться работоспособным и что перестанет? Укажи свойство конкретного L2 VNI, IP-VRF или маршрута.
2. **Baseline:** записать ping VPCS, `show ip ospf neighbors`, `show ip route`, `show bgp l2vpn evpn summary`, `show nve peers`, `show nve vni`, нужные VRF/route-type.
3. **Fault injection:** выполнить только один сценарий. При нераспознанном CLI остановиться и проверить синтаксис `?` именно своего NX-OS.
4. **Наблюдение:** сперва отделить физический линк / underlay / EVPN control / overlay dataplane / gateway / firewall. По возможности сохранить PCAP на EVE линках.
5. **Rollback:** откатить командой из карточки, затем вернуть baseline; только после этого переходить к следующему сценарию.
6. **Отчёт:** таблица времени, ожиданий, наблюдений, локализации, исправления, восстановления. Время конвергенции не предполагается заранее, измеряется на стенде.

**Ограничения:** существующие `.unl` не требуют изменения для сценариев 00–10,12. Для 11 нужны Linux-хосты вместо VPCS или дополнительный Linux-узел, сеть изолировать от внешних интерфейсов. Разбор исходного multicast Flood & Learn остаётся отдельным [материалом](../docs/legacy-multicast.md): PIM-SM/BIDIR не эмулируются в текущих конфигурациях.

**Шпаргалка:** [docs/SCENARIO-DIAGNOSTICS.md](../docs/SCENARIO-DIAGNOSTICS.md). На NX-OS с разной версией отдельные команды могут отличаться. Ни одна карточка не подтверждена end-to-end запуском на конкретном EVE-NG сервере.
