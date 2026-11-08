# 03 — Route leak / bypass of scrubbing

**Intentional temporary misconfiguration — run in isolated EVE lab only.** Baseline `R-CE` must not export protected /24 directly to ISP1.

## Step 1: Allow CE to export directly to ISP1

On **R-CE**:

```ios
conf t
 router bgp 65010
  no neighbor 198.18.11.1 prefix-list DENY-ALL out
  neighbor 198.18.11.1 prefix-list PROTECTED out
end
```

On **R-ISP1** allow protected prefix from CE and re-export it to T1:

```ios
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
```

On **R-T1** extend inbound whitelist for ISP1:

```ios
conf t
 ip prefix-list ISP1-IN seq 10 permit 203.0.113.0/24
end
```

R-T1 already has a `FROM-ISP1` inbound route map that assigns leaked protected prefix **local preference 350**. Its normal path from CUR1 has local preference 100; route through ISP1 now wins.

Check on R-T1: `show ip bgp 203.0.113.0` now selects AS_PATH `65011 65010`, **not** `65020 65010`. A CLIENT behind AS65031 now bypasses scrubbing (though CLIENT is allowed in baseline anyway).

To visibly demonstrate bypass from a blocked BOT behind AS65041/42, optionally prefer the leaked route at **R-T2**:

```ios
conf t
 route-map PREFER-LEAK permit 10
  match ip address prefix-list PROTECTED
  set local-preference 400
 route-map PREFER-LEAK permit 20
  set local-preference 100
 router bgp 65001
  neighbor 10.1.0.1 route-map PREFER-LEAK in
end
```

After policy refresh (or soft inbound route refresh), R-T2 prefers the longer leaked route via T1, and a BOT1/BOT2 ICMP echo may pass because the path bypasses CUR1/CUR2 ACLs. Check `show ip route 203.0.113.10`, traceroute and POP ACL counters. **Do not assume policy took effect without checking BGP best-path.**

## Restore clean config

Reverse the steps, or simply reapply baseline `.cfg` after `write erase`/reload of nodes **only inside this lab**. For production devices this is inappropriate. More specifically:

- CE: export `DENY-ALL` to ISP1, remove `PROTECTED` filter.
- ISP1: filter `DENY-ALL` inbound CE; restore `ISP1-EXPORT` outbound T1.
- T1: delete `ip prefix-list ISP1-IN seq 10`.
- T2: remove `neighbor 10.1.0.1 route-map PREFER-LEAK in` if added.

Recheck BGP and pop filtering. Documentation: `https://docs.curator.pro/connect/bgp.html`.
