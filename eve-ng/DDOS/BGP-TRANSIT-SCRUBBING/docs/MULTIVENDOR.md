# CE-A на Junos / MikroTik: вариант расширения

Импортируемый .unl и startup-config предназначены для IOSv. Чтобы проверить знание другого вендора, **замените только CE-A** на vJunos-router/vMX или MikroTik CHR, сохранив назначение интерфейсов. Эти варианты не проверялись в виртуальном стенде; сверяйте синтаксис с точным релизом и шаблоном EVE.

## IP и BGP contract
| Interface | IP | Peer |
| --- | --- | --- |
| Uplink PE1 | 10.20.0.2/30 | 10.20.0.1, AS65000 |
| Uplink PE2 | 10.20.0.6/30 | 10.20.0.5, AS65000 |
| LAN | 203.0.113.1/24 | 203.0.113.0/24 originate |

Local AS клиента: 65010. Импортировать только 198.51.100.0/24, экспортировать только 203.0.113.0/24; предпочтение PE1 и failover.

### Junos (адаптировать имена ge-0/0/x)
```text
set system host-name CE-A
set interfaces ge-0/0/0 unit 0 family inet address 10.20.0.2/30
set interfaces ge-0/0/1 unit 0 family inet address 10.20.0.6/30
set interfaces ge-0/0/2 unit 0 family inet address 203.0.113.1/24
set routing-options autonomous-system 65010
set policy-options policy-statement EXPORT-CE term 1 from route-filter 203.0.113.0/24 exact
set policy-options policy-statement EXPORT-CE term 1 then accept
set policy-options policy-statement EXPORT-CE term DENY then reject
set policy-options policy-statement IMPORT-A term 1 from route-filter 198.51.100.0/24 exact
set policy-options policy-statement IMPORT-A term 1 then local-preference 200
set policy-options policy-statement IMPORT-A term 1 then accept
set policy-options policy-statement IMPORT-A term DENY then reject
set policy-options policy-statement IMPORT-B term 1 from route-filter 198.51.100.0/24 exact
set policy-options policy-statement IMPORT-B term 1 then accept
set policy-options policy-statement IMPORT-B term DENY then reject
set protocols bgp group TRANSIT type external
set protocols bgp group TRANSIT export EXPORT-CE
set protocols bgp group TRANSIT neighbor 10.20.0.1 peer-as 65000
set protocols bgp group TRANSIT neighbor 10.20.0.1 import IMPORT-A
set protocols bgp group TRANSIT neighbor 10.20.0.5 peer-as 65000
set protocols bgp group TRANSIT neighbor 10.20.0.5 import IMPORT-B
commit confirmed 5
```
При проверке всё должно быть видно в inet.0; после подтверждения конфигурации выполните `commit`, иначе Junos выполнит rollback. Для vSRX дополнительно проверить security zones / разрешённый BGP на интерфейсах.

### RouterOS v7: тренировочный шаблон, не проверен на вашем minor release
```routeros
/ip/address/add address=10.20.0.2/30 interface=ether1
/ip/address/add address=10.20.0.6/30 interface=ether2
/ip/address/add address=203.0.113.1/24 interface=ether3
/ip/firewall/address-list/add list=bgp-export address=203.0.113.0/24
/routing/filter/rule/add chain=IN-A rule="if (dst == 198.51.100.0/24) { set bgp-local-pref 200; accept; }"
/routing/filter/rule/add chain=IN-A rule="reject"
/routing/filter/rule/add chain=IN-B rule="if (dst == 198.51.100.0/24) { accept; }"
/routing/filter/rule/add chain=IN-B rule="reject"
/routing/filter/rule/add chain=OUT rule="if (dst == 203.0.113.0/24) { accept; }"
/routing/filter/rule/add chain=OUT rule="reject"
/routing/bgp/template/add name=CLIENT as=65010 router-id=203.0.113.1
/routing/bgp/connection/add name=UP-A remote.address=10.20.0.1 remote.as=65000 local.role=ebgp templates=CLIENT input.filter-chain=IN-A output.filter-chain=OUT output.network=bgp-export
/routing/bgp/connection/add name=UP-B remote.address=10.20.0.5 remote.as=65000 local.role=ebgp templates=CLIENT input.filter-chain=IN-B output.filter-chain=OUT output.network=bgp-export
```
У RouterOS v7 свойства `connection/template` и BGP фильтрации менялись между релизами. До применения изучите `/routing/bgp/connection/print detail` и документацию именно своей версии. Контроль: `/routing/bgp/session/print detail`, маршрут, фильтры, egress pings, failover. Junos/RouterOS конфигурации — факультативные учебные примеры, не обещание готового bootable шаблона.
