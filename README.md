# NetLabs

Коллекция лабораторных работ по сетевым технологиям для **EVE-NG** и **GNS3**: маршрутизация, MPLS, VXLAN/EVPN, BGP, VPN, отказоустойчивость и диагностика.

Лаборатории предназначены для изучения протоколов, отработки конфигураций и поиска неисправностей. Новые практикумы EVE-NG содержат отдельные инструкции и сценарии; в архиве GNS3 часть работ представлена только конфигурациями и схемами.

## EVE-NG

| Раздел | Лаборатории | Что изучается |
|---|---|---|
| [L2](eve-ng/L2/README.md) | [MSTP Multi-Region](eve-ng/L2/STP/MSTP-Multi-Region/README.md) | 3 MST-региона, CIST/IST, MSTI1, границы с Rapid-PVST, отказоустойчивость Ethernet |\n| [IGP](eve-ng/IGP/README.md) | [OSPF Multiarea](eve-ng/IGP/OSPF/OSPF%20Multiarea%20%28topology%201%29/) | Внутренние протоколы маршрутизации: OSPF; в дальнейшем — IS-IS и другие |
| [MPLS](eve-ng/MPLS/README.md) | [MPLS Service Provider Advanced](eve-ng/MPLS/MPLS%20Service%20Provider%20Advanced/README.md) | OSPF underlay, LDP, L3VPN, MP-BGP VPNv4, Route Reflector, VRF и отказоустойчивость |
| [VXLAN](eve-ng/VXLAN/README.md) | [VXLAN-FABRIC](eve-ng/VXLAN/VXLAN-FABRIC/README.md) | Leaf–Spine, OSPF, BGP EVPN, L2/L3 VNI, Symmetric IRB, VRF и сценарии отказов |
| [DDoS](eve-ng/DDOS/README.md) | [CURATOR-BGP-MULTIAS](eve-ng/DDOS/CURATOR-BGP-MULTIAS/README.md) | Multi-AS BGP, два транзитных оператора, GRE, два POP защиты, резервирование и проверка путей трафика |

**С чего начать:** [MSTP Multi-Region](eve-ng/L2/STP/MSTP-Multi-Region/README.md#быстрый-старт) · [импорт MPLS в EVE-NG](eve-ng/MPLS/MPLS%20Service%20Provider%20Advanced/IMPORT-RU.md) · [запуск VXLAN-FABRIC](eve-ng/VXLAN/VXLAN-FABRIC/README.md#требования-и-установка) · [сценарии DDoS-лаборатории](eve-ng/DDOS/CURATOR-BGP-MULTIAS/README.md#практические-сценарии).

## GNS3

Архив лабораторных работ и конфигураций. Не во всех каталогах есть файл проекта `.gns3`: иногда сохранены только схема и настройки устройств.

| Раздел | Лаборатории | Что изучается |
|---|---|---|
| [Basic](gns3/Basic/) | [Eltex MES basic](gns3/Basic/Eltex%20MES%20basic.txt) | Базовые настройки коммутаторов Eltex MES |
| [EGP](gns3/EGP/) | [BGP Route Reflector](gns3/EGP/BGP%20Topology%201_1%20%28RR%20cluster%29/), [BGP Confederation](gns3/EGP/BGP%20Topology%202%20%28confederation%29/) | BGP RR cluster и confederation |
| [IGP](gns3/IGP/) | [OSPF / OSPFv3](gns3/IGP/OSPF/), [IS-IS](gns3/IGP/ISIS/) | Внутренние протоколы маршрутизации, IPv6 и FRR |
| [MPLS](gns3/MPLS/) | [Basic](gns3/MPLS/Basic/), [CE–PE](gns3/MPLS/CE-PEs/), [Inter-AS](gns3/MPLS/Inter-AS/README.md), [L2VPN](gns3/MPLS/L2VPN/), [L3VPN](gns3/MPLS/L3VPN/) | MPLS core, межоператорские VPN, VPLS и PE–CE OSPF/EIGRP/BGP |
| [VXLAN](gns3/VXLAN/) | [Flood & Learn](gns3/VXLAN/VXLAN%20Topology%202%20%28F%26L%29/), [BIDIR](gns3/VXLAN/VXLAN%20Topology%202_1%20%28F%26L%20BIDIR%29/), [EVPN](gns3/VXLAN/VXLAN%20Topology%203_1%20%28EVPN%29/), [Multitenancy](gns3/VXLAN/VXLAN%20Topology%203_3%20%28Multitenancy%29/) | VXLAN Flood & Learn, EVPN и сегментация |
| [VPN](gns3/VPN/) | [DMVPN](gns3/VPN/DMVPN/), [IPsec](gns3/VPN/IPSec/) | IKEv1/IKEv2, site-to-site, hub-and-spoke и DMVPN |
| [MLAG](gns3/MLAG/) | [vPC](gns3/MLAG/VPC_1%20%28Rapid-PVST%29/) | Агрегация и резервирование каналов, Rapid-PVST |
| [STP](gns3/STP/) | [MSTP](gns3/STP/MSTP_1/) | Multiple Spanning Tree Protocol |
| [Ring](gns3/Ring/) | [ERPS (Eltex)](gns3/Ring/ERPS%20%28Eltex%29/) | Защита и восстановление Ethernet-кольца |
| [Diagram](gns3/Diagram/) | [Сетевые схемы](gns3/Diagram/) | Диаграммы в draw.io |

## Быстрый старт

1. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/thleontev/netlabs.git
   cd netlabs
   ```
2. Выберите платформу и лабораторию в таблицах выше. Прочитайте её `README.md` или инструкцию в каталоге, если она есть.
3. **EVE-NG:** импортируйте нужный `.unl`, проверьте имена QEMU-образов и настройки Startup-configs. Для некоторых лабораторий конфигурации уже встроены в `.unl`; для других их нужно загрузить вручную. Следуйте инструкции конкретной работы.
4. **GNS3:** откройте `.gns3`-проект, если он есть. Если проект не сохранён, соберите топологию по схеме `Topology.png` и примените конфигурации из каталога.
5. Проверьте соседства, таблицы маршрутизации и прохождение трафика; затем переходите к упражнениям и сценариям отказов (если предусмотрены).

**Важно:** образы Cisco, Nexus, Eltex и других устройств в репозиторий не включены. Нужны совместимые версии ПО и законно полученные образы. Названия интерфейсов, синтаксис команд и поведение startup-config могут зависеть от образа и версии эмулятора. Статическая проверка файлов не заменяет запуск и тестирование лаборатории.

## Организация репозитория

- `eve-ng/<технология>/<лаборатория>/` — файлы `.unl`, конфигурации, схемы, инструкции, сценарии и инструменты проверки (состав зависит от лаборатории).
- `gns3/<технология>/<лаборатория>/` — проекты `.gns3` (при наличии), изображения топологий и конфигурации устройств.

Подробные команды, адресация и критерии успешной проверки находятся в документации соответствующей лаборатории.

## Лицензия

См. [LICENSE](LICENSE).
