# NetLabs

Коллекция лабораторных работ по сетевым технологиям для **EVE-NG** и **GNS3**: маршрутизация, MPLS, VXLAN/EVPN, BGP, VPN, отказоустойчивость и диагностика.

Лаборатории предназначены для изучения протоколов, отработки конфигураций и поиска неисправностей. Новые практикумы EVE-NG содержат отдельные инструкции и сценарии; в архиве GNS3 часть работ представлена только конфигурациями и схемами.

## EVE-NG

| Раздел | Лаборатория | Что изучается |
|---|---|---|
| [IGP / OSPF](eve-ng/IGP/OSPF/) | [OSPF Multiarea](eve-ng/IGP/OSPF/OSPF%20Multiarea%20%28topology%201%29/) | Многообластная маршрутизация OSPF; проект `.unl`, конфигурации устройств и схема |
| [MPLS](eve-ng/MPLS/README.md) | [MPLS Service Provider Advanced](eve-ng/MPLS/MPLS%20Service%20Provider%20Advanced/README.md) | OSPF underlay, LDP, L3VPN, MP-BGP VPNv4, Route Reflector, VRF и отказоустойчивость |
| [VXLAN](eve-ng/VXLAN/README.md) | [VXLAN-FABRIC](eve-ng/VXLAN/VXLAN-FABRIC/README.md) | Leaf–Spine, OSPF, BGP EVPN, L2/L3 VNI, Symmetric IRB, VRF и сценарии отказов |
| [DDoS](eve-ng/DDOS/README.md) | [CURATOR-BGP-MULTIAS](eve-ng/DDOS/CURATOR-BGP-MULTIAS/README.md) | Multi-AS BGP, два транзитных оператора, GRE, два POP защиты, резервирование и проверка путей трафика |

**С чего начать:** [импорт MPLS в EVE-NG](eve-ng/MPLS/MPLS%20Service%20Provider%20Advanced/IMPORT-RU.md) · [запуск VXLAN-FABRIC](eve-ng/VXLAN/VXLAN-FABRIC/README.md#требования-и-установка) · [сценарии DDoS-лаборатории](eve-ng/DDOS/CURATOR-BGP-MULTIAS/README.md#практические-сценарии).

## GNS3

Архив лабораторных работ и конфигураций. Не во всех каталогах есть файл проекта `.gns3`: иногда сохранены только схема и настройки устройств.

| Раздел | Темы |
|---|---|
| [Basic](gns3/Basic/) | Базовые конфигурации, в том числе Eltex MES |
| [EGP / BGP](gns3/EGP/) | Route Reflector cluster, BGP confederation |
| [IGP](gns3/IGP/) | OSPF, OSPFv3, IS-IS для IPv6, FRR |
| [MPLS](gns3/MPLS/) | MPLS core, L3VPN с OSPF/EIGRP/BGP, [Inter-AS](gns3/MPLS/Inter-AS/README.md), VPLS |
| [VXLAN](gns3/VXLAN/) | Flood & Learn, BIDIR, EVPN и Multitenancy |
| [VPN](gns3/VPN/) | DMVPN, IPsec IKEv1/IKEv2, site-to-site и hub-and-spoke |
| [MLAG](gns3/MLAG/) | vPC и Rapid-PVST |
| [STP](gns3/STP/) | MSTP |
| [Ring](gns3/Ring/) | [ERPS на Eltex](gns3/Ring/ERPS%20%28Eltex%29/) |
| [Diagram](gns3/Diagram/) | Сетевые схемы в draw.io |

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
