#!/usr/bin/env bash
# Lab-only Debian firewall configuration (inside FW-LINUX VM, not on EVE host!)
set -euo pipefail
: "${CLIENT_IF:?Set CLIENT_IF=... after checking 'ip -br link'}"
: "${APPS_IF:?Set APPS_IF=... after checking 'ip -br link'}"
[[ "$CLIENT_IF" != "$APPS_IF" ]] || { echo 'Refusing: same NIC for both VRFs' >&2; exit 2; }
for nic in "$CLIENT_IF" "$APPS_IF"; do ip link show "$nic" >/dev/null || { echo "Missing $nic" >&2; exit 2; }; done
command -v nft >/dev/null || { echo 'nftables missing: apt install nftables' >&2; exit 2; }
for x in "$CLIENT_IF" "$APPS_IF"; do ip addr flush dev "$x"; ip link set "$x" up; done
ip addr add 172.31.10.2/30 dev "$CLIENT_IF"
ip addr add 172.31.20.2/30 dev "$APPS_IF"
ip route replace 192.168.10.0/24 via 172.31.10.1 dev "$CLIENT_IF"
ip route replace 192.168.20.0/24 via 172.31.20.1 dev "$APPS_IF"
ip route replace 192.168.30.0/24 via 172.31.20.1 dev "$APPS_IF"
sysctl -w net.ipv4.ip_forward=1
# Never wipe full nftables ruleset. Manage lab table only.
nft delete table inet vxlan_lab 2>/dev/null || true
nft add table inet vxlan_lab
nft 'add chain inet vxlan_lab forward { type filter hook forward priority 0; policy drop; }'
nft add rule inet vxlan_lab forward ct state established,related accept
nft add rule inet vxlan_lab forward iifname "$CLIENT_IF" oifname "$APPS_IF" ip saddr 192.168.10.0/24 ip daddr 192.168.20.0/24 meta l4proto icmp accept
nft add rule inet vxlan_lab forward iifname "$CLIENT_IF" oifname "$APPS_IF" ip saddr 192.168.10.0/24 ip daddr 192.168.30.0/24 meta l4proto icmp accept
# Firewall is a two-legged, non-NAT routed stateful zone boundary.
ip route show
nft list table inet vxlan_lab
