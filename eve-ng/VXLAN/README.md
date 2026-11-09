# VXLAN — лаборатории EVE-NG

Каталог предназначен для **нескольких независимых лабораторий по VXLAN**. Каждый проект размещается в собственной папке вместе с `.unl`, конфигурациями, схемами, сценариями и документацией.

## Лаборатории

### [VXLAN-FABRIC](VXLAN-FABRIC/README.md)

Leaf–Spine fabric на Cisco Nexus 9000v: **2 Spine, 3 Leaf, 6 VPCS**, OSPF underlay, BGP EVPN L2, Symmetric IRB, L3VNI, Multi-VRF, firewall, диагностика и 13 практических break/fix сценариев.

- [Основная лаборатория EVPN L2](VXLAN-FABRIC/VXLAN-FABRIC-5N-6H.unl)
- [Multitenancy без firewall](VXLAN-FABRIC/VXLAN-FABRIC-MULTITENANT-NOFW.unl)
- [Multitenancy с IOSv ACL-router](VXLAN-FABRIC/VXLAN-FABRIC-MULTITENANT-IOSV-FW.unl)
- [Multitenancy с Linux firewall](VXLAN-FABRIC/VXLAN-FABRIC-MULTITENANT-FW.unl)
- [Конфигурации по стадиям](VXLAN-FABRIC/configs/) · [Практические сценарии](VXLAN-FABRIC/scenarios/README.md) · [Диагностика](VXLAN-FABRIC/docs/SCENARIO-DIAGNOSTICS.md)

Встроенные startup-config предусмотрены в указанных `.unl` (их применение зависит от версии EVE-NG и QEMU-образа). Для варианта с Linux firewall требуется подготовленный Linux-образ; IOSv ACL-router **не является stateful firewall**. Проверку фактического запуска на конкретном сервере EVE-NG выполнять отдельно.

## Структура

```text
eve-ng/
└── VXLAN/
    ├── README.md                 # каталог лабораторий
    └── VXLAN-FABRIC/             # одна независимая лаборатория
        ├── README.md
        ├── *.unl
        ├── configs/
        ├── scenarios/
        ├── docs/
        ├── topology.json
        └── *.svg, *.png
```

Следующие VXLAN-лаборатории размещать **рядом с VXLAN-FABRIC**, не смешивая их файлы и сценарии. Существующие материалы были перенесены без перегенерации схем и `.unl`.
