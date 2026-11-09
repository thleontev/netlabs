# 03 — Утечка маршрута и обход центра очистки

**Цель:** показать, как ошибочный прямой анонс защищаемого префикса через обычного ISP может перенаправить трафик в обход фильтрации.

**Условия:** эксперимент выполняется только в изолированной лаборатории EVE-NG. В исходном состоянии `R-CE` не должен анонсировать `203.0.113.0/24` напрямую в ISP1.

## Задание 1. Разрешить прямой анонс от CE в ISP1

На `R-CE`:

~~~ios
conf t
 router bgp 65010
  no neighbor 198.18.11.1 prefix-list DENY-ALL out
  neighbor 198.18.11.1 prefix-list PROTECTED out
end
~~~

На `R-ISP1` разрешите получение защищаемого префикса от CE и его передачу в `R-T1`:

~~~ios
conf t
 ip prefix-list PROTECTED seq 5 permit 203.0.113.0/24
 ip prefix-list ISP1-LEAK seq 5 permit 198.18.11.0/30
 ip prefix-list ISP1-LEAK seq 10 permit 203.0.113.0/24
 router bgp 65011
  no neighbor 198.18.11.2 prefix-list DENY-ALL in
  neighbor 198.18.11.2 prefix-list PROTECTED in
  no neighbor 10.1.0.9 prefix-list ISP1-EXPORT out
  neighbor 10.1.0.9 prefix-list ISP1-LEAK out
end
~~~

На `R-T1` добавьте защищаемый префикс во входной список разрешённых маршрутов ISP1:

~~~ios
conf t
 ip prefix-list ISP1-IN seq 10 permit 203.0.113.0/24
end
~~~

## Задание 2. Проверить выбор маршрута

На `R-T1` уже используется входная `route-map FROM-ISP1`, которая назначает утёкшему маршруту `local-preference 350`. Обычный путь через CUR1 имеет `local-preference 100`, поэтому при корректном применении политик предпочтение получит ISP1.

Командой `show ip bgp 203.0.113.0` убедитесь, что выбран `AS_PATH 65011 65010` вместо `65020 65010`. Трафик от `CLIENT` в таком случае обходит POP и его ACL.

## Задание 3. Проверить обход со стороны тестовых источников

Чтобы увидеть эффект на трафике, который обычно блокируется, можно **временно** предпочесть утёкший маршрут на `R-T2`:

~~~ios
conf t
 route-map PREFER-LEAK permit 10
  match ip address prefix-list PROTECTED
  set local-preference 400
 route-map PREFER-LEAK permit 20
  set local-preference 100
 router bgp 65001
  neighbor 10.1.0.1 route-map PREFER-LEAK in
end
~~~

После обновления маршрутов BGP проверьте лучший путь на `R-T2`. При выборе пути через `R-T1/ISP1` ICMP-запросы `BOT1` и `BOT2` могут достичь сервера в обход ACL двух POP.

Используйте `show ip route 203.0.113.10`, трассировку и счётчики `show access-lists SCRUB-POLICY`. **Не считайте обход подтверждённым, пока не проверен лучший маршрут BGP и фактический путь пакетов.**

## Восстановление исходных политик

- На `R-CE` верните выходной фильтр `DENY-ALL` в сторону ISP1 и отмените экспорт `PROTECTED`.
- На `R-ISP1` восстановите входной `DENY-ALL` со стороны CE и выходной `ISP1-EXPORT` в сторону T1.
- На `R-T1` удалите `ip prefix-list ISP1-IN seq 10`.
- На `R-T2`, если изменяли политику, удалите `neighbor 10.1.0.1 route-map PREFER-LEAK in`.
- Повторно проверьте BGP и работу фильтрации на POP.

При необходимости восстановите исходные конфигурации из `configs/*.cfg` **только на узлах этой лаборатории**. Не применяйте стирание конфигурации к реальным устройствам.

Справка: https://docs.curator.pro/connect/bgp.html
