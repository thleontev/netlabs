# OSPF Multiarea (topology 1) — EVE-NG

Существующая лаборатория многообластного OSPF на Cisco IOSv и IOS XRv: магистральная область, ABR, virtual link, stub, NSSA и взаимодействие с EIGRP AS 100.

**Состав:** 14 устройств (8 IOSv, 4 IOS XRv, 2 IOSvL2) и 15 сетевых сегментов. В исходном `ospf_multiarea.unl` у 14 узлов установлен `config="1"`, а startup-config записаны непосредственно в XML.

**Принцип изменений:** обновлена **только организация файлов и документация**. Содержимое `.unl`, исходных конфигураций и PNG-схемы сохранено без изменений; `.txt` переименованы в `.cfg`. Фактическая работа оборудования в EVE-NG не проверялась.

## Топология

![OSPF Multiarea — исходная схема](docs/topology.png)

[Открыть схему PNG](docs/topology.png) · [Файл EVE-NG](ospf_multiarea.unl)

Устройства: R5–R12 (IOSv), XR1–XR4 (IOS XRv), SW1 и SW2 (IOSvL2). Коммутаторы SW1/SW2 обеспечивают L2-сегменты.

## Состав лаборатории

| Область / протокол | Назначение |
|---|---|
| OSPF area 0 | Backbone между XR1, XR3, R6, R7 и R8 |
| OSPF area 100 | XR1–XR4 и R5; связь с магистралью через ABR |
| OSPF area 51 | Stub между XR1 и R11 |
| OSPF area 200 | R6–R10; virtual link через транзитную область |
| OSPF area 300 | NSSA между R8 и R12; редистрибуция connected на R12 |
| EIGRP 100 | Соседство XR2–R9 и взаимная редистрибуция с OSPF на XR2 |

В исходных конфигурациях есть MD5-аутентификация, key-chain и особые параметры Hello/Dead на некоторых соединениях. Это описание файлов, а не подтверждение работающих OSPF-соседств.

## Структура файлов

```text
OSPF Multiarea (topology 1)/
├── README.md
├── IMPORT-RU.md
├── ospf_multiarea.unl
├── configs/
│   ├── R5.cfg ... R12.cfg
│   ├── XR1.cfg ... XR4.cfg
│   ├── SW1.cfg
│   └── SW2.cfg
└── docs/
    ├── topology.png
    ├── DIAGNOSTICS.md
    └── EXERCISES.md
```

| Путь | Назначение |
|---|---|
| [`ospf_multiarea.unl`](ospf_multiarea.unl) | Исходная лаборатория с 14 встроенными startup-config |
| [`configs/`](configs/) | Отдельные исходные конфигурации Cisco IOSv, IOS XRv, IOSvL2 в формате `.cfg` |
| [`docs/topology.png`](docs/topology.png) | Исходная схема топологии (без перерисовки) |
| [`IMPORT-RU.md`](IMPORT-RU.md) | Импорт и запуск EVE-NG CE |
| [`docs/DIAGNOSTICS.md`](docs/DIAGNOSTICS.md) | Команды проверки соседств, LSDB, маршрутов, редистрибуции |
| [`docs/EXERCISES.md`](docs/EXERCISES.md) | Последовательность учебных проверок на существующей топологии |

Файлы `configs/*.cfg` — **отдельные сохранённые конфигурации**, которые удобно читать и сравнивать. EVE-NG не загружает их из папки автоматически: при первом запуске используются конфигурации, уже встроенные в `.unl`. Содержимое обоих наборов не объявляется идентичным без отдельной проверки. `configs/SW2.cfg` намеренно оставлен пустым, как и исходный `SW2.txt`.

## Быстрый старт

1. Подготовьте образы IOSv, IOSvL2 и IOS XRv (образы не распространяются в репозитории).
2. Откройте [IMPORT-RU.md](IMPORT-RU.md) и загрузите `ospf_multiarea.unl` на EVE-NG.
3. До запуска убедитесь, что встроенные startup-config доступны и включены в EVE-NG.
4. Проверьте соседства командами из [DIAGNOSTICS.md](docs/DIAGNOSTICS.md); затем выполните [упражнения](docs/EXERCISES.md).

**Ресурсы:** в `.unl` суммарно выделено 22 ГиБ RAM гостевым устройствам (8 × 1 ГиБ IOSv, 2 × 1 ГиБ IOSvL2, 4 × 3 ГиБ XRv), плюс ресурсы EVE-NG/гипервизора.

**Важно:** при повторном запуске старых виртуальных дисков предыдущие конфигурации могут сохраниться в NVRAM. `Wipe` удаляет состояние узла; сначала сохраните собственные изменения.

[← Каталог OSPF](../README.md)
