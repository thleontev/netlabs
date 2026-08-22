# NetLabs

Воспроизводимые лабораторные стенды EVE-NG и GNS3 для проверки NetCfg.

```text
eve-ng/labs/                 .unl-топологии
eve-ng/configs-sanitized/    обезличенные стартовые конфигурации
gns3/projects/               проекты GNS3
gns3/appliance-templates/    шаблоны устройств
scenarios/                   проверяемые сценарии
inventories/                 example inventories
docs/                        manifest образов и инструкция запуска
```

Не добавляйте образы сетевых ОС, реальные конфигурации, password hash, ключи, packet capture с производственной сети и снимки дисков. В `docs/image-manifest.md` фиксируйте поставщика, семейство, версию, хэш и легальный источник образа.
