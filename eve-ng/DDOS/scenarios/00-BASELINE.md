# 00 — Baseline / packet path

1. Start routers first, paste matching `configs/R-*.cfg` into the correct IOSv console, `write memory`. Initialize the four VPCS per `vpcs/`.
2. On R-CUR1, R-CUR2 and R-CUR-RR: `show ip ospf neighbor`, `show ip route ospf`.
3. BGP: `show ip bgp summary` on all 11 routers. On CE expect 4 eBGP neighbors: two physical ISP and two GRE POP.
4. On CE: `show ip route 198.18.0.21`, `show ip route 198.18.0.22`. These must resolve via **physical ISP1/ISP2** (/32 static), not via a tunnel.
5. On R-T1 and R-T2: `show ip bgp 203.0.113.0`. AS_PATH via local POP should be `65020 65010`.
6. On R-ACCESS-CLIENT: AS_PATH for 203.0.113.0/24 should be `65000 65020 65010`. On BOT1/BOT2 access routers should be `65001 65020 65010`.
7. VPCS CLIENT: `ping 203.0.113.10` succeeds. BOT1/BOT2 ping should fail by POP ACL. Check counters with `show access-lists SCRUB-POLICY` on both POPs.
8. Capture CE↔ISP1 or CE↔ISP2: decode GRE outer source/destination and internal packet. Capture from POP's ingress shows ordinary IP packet before GRE.

**Important:** VPCS does not perform HTTP/HTTPS. To test a web service use optional Linux variant from `linux/SETUP.md`. Default return route on CE prefers CUR1; when ingress is CUR2, the return path may be asymmetric. See `04-RETURN-PATH.md`.
