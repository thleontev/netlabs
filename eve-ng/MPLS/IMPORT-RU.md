# Исправление автозагрузки конфигураций — MPLS SP Advanced 2.1

**Причина:** прежняя `.unl` включала только топологию, все узлы имели `config="0"` и `<configs/>` оставался пустым. Отдельные `.cfg` в ZIP EVE-NG не загружает автоматически.

**Исправлено:** в каждой из трёх новых `.unl` параметр `config="1"` установлен у всех 16 Cisco IOSv, а их настройки встроены в `<objects><configs>` в Base64. Подготовлены именно startup-config, без интерактивных команд `enable` и `configure terminal`.

## Какой файл выбрать

- `MPLS-SP-Advanced-AUTO-L3VPN.unl` — **рекомендуется**: полный OSPF, LDP, MPLS L3VPN, MP-BGP VPNv4, RR, VRF, eBGP.
- `MPLS-SP-Advanced-AUTO-LDP.unl` — OSPF + LDP/MPLS, без L3VPN.
- `MPLS-SP-Advanced-AUTO-UNDERLAY.unl` — только IP/OSPF, для самостоятельной настройки MPLS.

Все три лаборатории независимые, со своими UUID. Их можно импортировать рядом со старой лабораторией, не перезаписывая её.

## Установка новой версии (EVE-NG CE)

На компьютере с распакованным архивом (PowerShell):

```powershell
scp .\MPLS-SP-Advanced-AUTO-L3VPN.unl root@192.168.0.100:/opt/unetlab/labs/
```

На EVE-NG (SSH):

```bash
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions
```

В браузере:

1. Открой новую лабораторию **MPLS-SP-Advanced-L3VPN-AUTO**.
2. В левом меню открой **Startup-configs**. У 16 узлов должны отображаться настройки, а переключатель автозагрузки должен быть **ON**.
3. Если запускал эти узлы раньше, сохрани нужные изменения, останови и **Wipe** их. Операция уничтожит содержимое виртуальных дисков/текущие NVRAM-состояния. Для новой лаборатории с отдельным UUID это, как правило, не нужно.
4. Запусти устройства, сначала P1 и PE-W1, затем остальные.

**Важно:** если имя папки образа отличается, проверь:

```bash
ls -1 /opt/unetlab/addons/qemu/ | grep '^vios-'
```

В файле указано `vios-adventerprisek9-m.SPA.159-3.M6`. Для замены без потери встроенных startup-config:

```powershell
py tools/rewrite_image.py --input MPLS-SP-Advanced-AUTO-L3VPN.unl --image vios-ИМЯ_ВАШЕЙ_ПАПКИ --output MPLS-SP-Advanced-AUTO-L3VPN-local.unl
```

После загрузки на PE-W1 проверь:

```text
show running-config | include hostname
show ip ospf neighbor
show mpls ldp neighbor
show bgp vpnv4 unicast all summary
show ip route vrf CUST_A
```

На CE-A-W1:

```text
show ip bgp summary
ping 10.100.4.1 source Loopback0
```

Сначала убедись, что `hostname` совпадает с именем узла. Если `show running-config` пустой, проблема уже на этапе использования startup-config: смотри **Startup-configs / ON**, наличие и правильность образа, чистый запуск после Wipe. Если hostname и интерфейсы появились, но не поднялись соседи — это отдельная проблема протоколов или совместимости IOSv.

## Проверки комплектности (только офлайн)

```bash
python3 tools/validate_startup_configs.py
python3 tools/validate_lab.py
```

Первый тест декодирует все 48 встроенных startup-config, сверяет с исходными конфигурациями, ID узлов и флагом `config=1`; второй тест проверяет 16 устройств, 23 канала связи, физическую адресацию и маршруты в модели.

**Граница проверки:** мы не запускали IOSv на твоём EVE-NG. Факт, что все 16 устройств поднимутся с нужными настройками и VPN заработает, нужно подтвердить в EVE.