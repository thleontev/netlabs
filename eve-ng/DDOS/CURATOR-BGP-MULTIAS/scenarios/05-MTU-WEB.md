# 05 — Linux web tests, MTU / TCP MSS

Use the optional Linux `.unl` generated as in `linux/SETUP.md` (replaces CLIENT, BOT2, SERVER). Configure static addresses and a Python web server on TCP/80.

Expected:
- Linux CLIENT `curl http://203.0.113.10/` receives HTTP 200.
- Linux BOT2 `curl --max-time 5 http://203.0.113.10/` times out on TCP due to POP ingress ACL. This is **source-based ACL**, not WAF/behavior analysis.
- ACL counters on POP2 increment for BOT2.
- Capture ISP-to-CE: GRE protocol 47 outer header, internal TCP segments; use Wireshark display filter `gre`.
- Verify effective GRE PMTU and MSS (`ip mtu 1476` and `ip tcp adjust-mss 1436` in supplied router configs). Test controlled DF probes; not every Linux image contains `ping -M do`.

Do not run unbounded traffic flood generators. This training lab does not replicate real-world volumetric capacity or provider mitigation algorithms.
