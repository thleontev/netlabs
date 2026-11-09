# 02 — Loss of POP1 transit connection

On **R-T1** shut down Gi0/1 (towards CUR1):

```ios
conf t
 interface GigabitEthernet0/1
  shutdown
end
```

This removes external R-T1 ↔ CUR1 BGP. After reconvergence, AS65000 may reach 203.0.113.0/24 via **AS65001 → CUR2**. Confirm `show ip bgp 203.0.113.0` on R-T1 and R-ACCESS-CLIENT; expected longer AS_PATH from client `65000 65001 65020 65010`. Expect GRE1 to lose underlay reachability and CE to use GRE2 after hold timeout.

Restore `no shutdown` on R-T1 Gi0/1.

Also test failure of the **T1–T2** link, but do this as a separate experiment: some source ASes will lose reachability to remote POPs; the baseline topology has only one inter-transit peering, so it is not a fully meshed global Internet. See README limitations.
