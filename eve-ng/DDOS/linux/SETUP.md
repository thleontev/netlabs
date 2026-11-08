# Optional Linux mode (CLIENT, BOT2, SERVER)

This is a *separate generated `.unl`*, not the default VPCS lab. You need an **already installed** EVE-NG QEMU Linux image (directory starts with `linux-`). Do not assume the example image name exists.

Create topology on PC:

```bash
python3 tools/build_lab.py \
  --image 'ACTUAL_vios_DIRECTORY' \
  --linux-image 'ACTUAL_linux_DIRECTORY' \
  --output CURATOR-BGP-MULTIAS-V3-LINUX.unl
python3 tools/check_lab.py CURATOR-BGP-MULTIAS-V3-LINUX.unl
```

Linux network device names differ. Use `ip -br link` to identify the actual NIC (e.g. `ens3`). These commands assume `ens3`. Do not execute if that interface is your existing management interface.

**CLIENT**

```bash
sudo ip addr add 198.18.100.10/24 dev ens3
sudo ip link set ens3 up
sudo ip route replace default via 198.18.100.1
curl --max-time 5 -v http://203.0.113.10/
```

**BOT2 (only bounded, authorized tests on this isolated lab)**

```bash
sudo ip addr add 198.18.102.10/24 dev ens3
sudo ip link set ens3 up
sudo ip route replace default via 198.18.102.1
curl --max-time 5 -v http://203.0.113.10/
```

**SERVER**

```bash
sudo ip addr add 203.0.113.10/24 dev ens3
sudo ip link set ens3 up
sudo ip route replace default via 203.0.113.1
sudo python3 -m http.server 80 --bind 203.0.113.10
```

When the source IPs match those in the baseline ACL, CLIENT HTTP should work while BOT2 HTTP is dropped by the ingress ACL of its POP. This is *not* genuine HTTP-layer WAF behavior. Inspect `show access-lists SCRUB-POLICY` to confirm counters. Host firewalls may need adjustment; do not change real network firewall policies.

**MTU:** GRE adds overhead; `ip mtu 1476` and TCP MSS 1436 on tunnels are starting values for 1500-byte underlay without additional encapsulation. Verify with DF-bit ping and packet capture.
