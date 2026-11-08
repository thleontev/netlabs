# 04 — Asymmetric return path, PBR exercise

The baseline CE receives default routes from both GRE POPs and from two ISPs. `local-preference` intentionally selects CUR1 as its primary return path. Traffic from T2 clients enters POP2 by default, therefore outbound return *can be asymmetric*. This is intentional so you can detect it.

Packet capture ingress from BOT1 → CUR2/GRE2 and return from SERVER → CE → GRE1/CUR1. If that happens, prove it with traceroute/capture and inspect potential stateful filtering issues.

## Optional: destination-specific PBR on the server-facing CE interface

**Try only after baseline is working**, because some IOSv images differ in PBR support. Ingress on Gi0/2 is from SERVER (not from the Internet!).

```ios
conf t
 ip access-list extended TO-CLIENT-AS
  permit ip 203.0.113.0 0.0.0.255 198.18.100.0 0.0.0.255
 ip access-list extended TO-BOT-AS
  permit ip 203.0.113.0 0.0.0.255 198.18.101.0 0.0.0.255
  permit ip 203.0.113.0 0.0.0.255 198.18.102.0 0.0.0.255
 route-map SERVER-RETURN permit 10
  match ip address TO-CLIENT-AS
  set ip next-hop 172.31.1.1
 route-map SERVER-RETURN permit 20
  match ip address TO-BOT-AS
  set ip next-hop 172.31.2.1
 route-map SERVER-RETURN permit 100
 interface GigabitEthernet0/2
  ip policy route-map SERVER-RETURN
end
```

Expected in healthy baseline: replies to AS65031 go to GRE1; replies to AS65041/42 to GRE2. Verify `show ip policy`, `show route-map SERVER-RETURN` and pcap. Note: this is a **simplified PBR**; during GRE failure it can override the otherwise healthy alternate default route until PBR next-hop availability changes. Production designs need track-based failover, per-VRF designs or other tested mechanisms. Do not treat this as production-ready PBR.

Remove using `no ip policy route-map SERVER-RETURN` under Gi0/2. Ensure failover is still tested both with PBR and without it.
