# Продолжение MPLS-SP Advanced: следующие самостоятельные лабы

**Эти модули пока не реализованы в .unl.** Они запланированы как последующее развитие базовых 16 IOSv-узлов, не стоит считать их частью `configs/02-l3vpn`.

| Приоритет | Расширение | Новые устройства / образ | Цель |
|---|---|---|---|
| 1 | Inter-AS L3VPN Option A | ASBR-65000, ASBR-65100, 2–3 роутера удалённой AS | Back-to-back VRF, IPv4 eBGP между ASBR, без MPLS на межоператорском интерфейсе |
| 2 | Inter-AS Option B / C | IOS XRv / XRv9k | MP-eBGP VPNv4 на ASBR (B); RR-to-RR MP-eBGP / BGP-LU и end-to-end PE next-hop (C) |
| 3 | Traffic Engineering | IOSv RSVP-TE или верифицированный IOS XR | RSVP signaling, explicit/dynamic tunnels, контроль bandwidth/path, сравнение с обычным IGP |
| 4 | PE–CE OSPF | IOSv PE + CE | OSPF domain-id / DN bit, backdoor link, sham link (по поддержке образа) |
| 5 | VPWS / L2VPN | IOSv (проверить EoMPLS на выбранном образе) | Псевдопровод и data-plane forwarding для Ethernet без VRF |
| 6 | EVPN-MPLS / Segment Routing | Платформа с подтверждённой поддержкой | BGP EVPN AF, EVPN-VPWS, SR-MPLS SID, TI-LFA, SR Policy |
| 7 | Inter-AS and security | ASBR и PE | VPN route leaks, max-prefix, BGP route-policy validation, ACL/control-plane hardening |

В старом `netlabs` уже есть Inter-AS A/B-1/B-2/C, L2VPN и RSVP-TE — можно использовать их как референсы при подготовке следующих самостоятельных `.unl`, сохранив существующую подложку.

**Нельзя смешивать IOS XR и классический IOS конфиги:** синтаксис интерфейсов, OSPF, MPLS и MP-BGP различается. Также нельзя считать, что IOSv реализует VPLS или BFD (Cisco CML IOSv docs прямо относит их к unsupported).
