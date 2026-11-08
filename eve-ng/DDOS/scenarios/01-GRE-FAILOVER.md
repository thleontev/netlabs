# 01 — Loss of GRE1, backup via internal CURATOR backbone

Baseline: verify `show ip bgp 203.0.113.0` on both POPs, `show ip route 203.0.113.0` and iBGP peering with R-CUR-RR.

On **R-CUR1**:

```ios
conf t
 interface Tunnel1
  shutdown
end
```

Expected after BGP hold timer expiry:
- CE loses eBGP to POP1, prefers default via POP2/GRE2.
- POP2 continues learning protected /24 directly from CE and shares it with RR via iBGP (`next-hop-self`).
- POP1 can continue advertising protected /24 to T1, but forwards it **internally via R-CUR-RR to POP2**, which sends it down GRE2.
- Trace PCAP on the CUR1→RR and RR→CUR2 segments to prove internal fallback, not automatic reroute at R-T1.

**Limitations:** Tunnel interface line protocol may not reflect data-plane health for all failure types; do not assume GRE alone provides liveness. Check BGP, RIB and actual packets.

Restore:

```ios
conf t
 interface Tunnel1
  no shutdown
end
```
