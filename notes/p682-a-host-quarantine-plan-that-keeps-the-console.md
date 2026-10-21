---
id: p682
title: "A host quarantine plan that keeps the console"
slug: a-host-quarantine-plan-that-keeps-the-console
sections: [it, devsecops]
topic: "Python scripts"
tags: [IncidentResponse, Python, Linux, SRE, CyberSecurity]
source: "LinkedIn post P682 · IR series"
linkedin_date: 2031-02-04
design: code
script: quarantine_plan.py
---

# A host quarantine plan that keeps the console

At 02:40 you cut the host off the network. At 02:41 the SSH session you are fixing it from freezes, and the box becomes a black hole.

## Quick reference

The full script is at the end of this note: `quarantine_plan.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 quarantine_plan.py inv.json pol.json --host web-01
```

**Example output**

```text
KEEP mgmt 10.20.0.0/24 tcp/22
READY 7 rules, management path first
```

## Explained

### What it does

`quarantine_plan.py` reads a host inventory and an isolation policy and builds the ruleset that cuts east-west traffic while keeping the management path open. The management accept is emitted before every drop, and the policy is drop. A policy with no management source is refused: exit 1. Bad JSON, an unknown host or a bad CIDR is exit 2.

### What the screen shows

The panel checks the management source, then builds the accept rules before the cut. It prints KEEP mgmt 10.20.0.0/24 tcp/22 and READY 7 rules, management path first.

### How to run it

`python3 quarantine_plan.py inventory.json policy.json --host web-01`. Add `--iptables` for a host without nft. `--apply` writes the ruleset with mode 0600 and prints `nft -f <file>`; it never loads it. The cron line is in the docstring.

### The fix

Put the console first. The plan allows the management subnet on tcp/22, then drops the private ranges both ways. If the console is serial or IPMI, add it as a management source.

### Prevention

Keep the policy beside the inventory, and review it with the on-call console subnet in the diff. Check the rendered ruleset with `nft -c -f` before it reaches a host.

> **The honest caveat:** it knows the paths in the policy, not the out-of-band console you forgot to list.

> **The lesson:** a quarantine that locks you out is an outage with a story.

## In one line

> **Seal the host, keep the door.** A quarantine that locks you out is an outage with a story.

**Plan first**

```bash
python3 quarantine_plan.py inv.json pol.json
```

## Script: quarantine_plan.py

Download: [scripts/quarantine_plan.py](../scripts/quarantine_plan.py)

```python
#!/usr/bin/env python3
"""quarantine_plan.py - build a host quarantine ruleset that keeps the console.

Reads a host inventory and an isolation policy, then prints the nftables (or
iptables) rules that cut east-west traffic while keeping the management path
open. The management accept rule is emitted first and the chain default is
drop, so the printed order is the whole argument.

The default is a dry run: it prints the plan and writes nothing. --apply
writes the ruleset to a file with mode 0600 and prints the command that loads
it (nft -f or sh). It never runs a firewall command itself.

Usage:
  ./quarantine_plan.py inventory.json policy.json --host web-01
  ./quarantine_plan.py inventory.json policy.json --host web-01 --iptables
  ./quarantine_plan.py inventory.json policy.json --host web-01 \
      --apply --out /root/quarantine.nft

Cron / CI (render the plan on every inventory change, never apply):
  30 * * * * /usr/local/bin/quarantine_plan.py /etc/ir/inventory.json \
    /etc/ir/policy.json --host web-01 >> /var/log/quarantine_plan.log 2>&1

Exit codes:
  0  plan built and the management rule is present and first
  1  refused: no management source, so the plan would cut the console
  2  usage error, unreadable JSON, unknown host, bad address or port

The ruleset is IPv4. An IPv6 cut is a usage error, not a rule that silently
does nothing.

Inventory: {"hosts": [{"name": "web-01", "ip": "10.20.4.11"}, ...]}
Policy: {"management": {"sources": ["10.20.0.0/24"], "port": 22,
         "proto": "tcp"},
         "keep_egress": [{"to": "10.20.0.10", "port": 53, "proto": "udp"}],
         "cut": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]}

By s0sta.com
"""
import argparse
import ipaddress
import json
import os
import re
import sys

DEFAULT_CUT = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
               "169.254.0.0/16"]


def die(msg):
    print("ERROR " + msg, file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        die("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        die("%s: not valid JSON (%s)" % (path, exc))


def net(value, label):
    try:
        return ipaddress.ip_network(str(value), strict=False)
    except ValueError:
        die("%s: not a CIDR: %s" % (label, value))


def net4(value, label):
    n = net(value, label)
    if n.version != 4:
        die("%s: IPv6 is not supported in this IPv4 ruleset: %s" % (label, value))
    return n


def port(value, label):
    try:
        n = int(value)
    except (TypeError, ValueError):
        die("%s: not a port: %s" % (label, value))
    if not 1 <= n <= 65535:
        die("%s: port out of range: %s" % (label, value))
    return n


def main():
    ap = argparse.ArgumentParser(
        description="Print the nftables or iptables rules that quarantine a "
                    "host and keep its management path.")
    ap.add_argument("inventory", help="host inventory JSON")
    ap.add_argument("policy", help="isolation policy JSON")
    ap.add_argument("--host", required=True, help="host name in the inventory")
    ap.add_argument("--iptables", action="store_true",
                    help="emit iptables commands instead of an nft ruleset")
    ap.add_argument("--table", default="ir_quarantine",
                    help="nftables table name (default: ir_quarantine)")
    ap.add_argument("--apply", action="store_true",
                    help="write the ruleset file; nothing is loaded")
    ap.add_argument("--out", default=None,
                    help="ruleset path for --apply (default /tmp/quarantine-<host>)")
    ap.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = ap.parse_args()

    table = args.table.strip()
    if not re.match(r"^[A-Za-z0-9_]+$", table):
        die("--table must be letters, digits or underscore: %s" % args.table)

    inv = load(args.inventory)
    pol = load(args.policy)
    hosts = inv.get("hosts", inv) if isinstance(inv, dict) else inv
    if not isinstance(hosts, list):
        die("inventory: expected a list under 'hosts'")
    match = None
    for h in hosts:
        if isinstance(h, dict) and str(h.get("name", "")) == args.host:
            match = h
            break
    if match is None:
        die("host %s not in %s" % (args.host, args.inventory))
    ip = str(match.get("ip") or match.get("address") or "unknown")
    if ip != "unknown":
        net4(ip, "inventory host ip")

    if not isinstance(pol, dict):
        die("policy: expected a JSON object")
    mgmt = pol.get("management") or {}
    if not isinstance(mgmt, dict):
        die("policy: management must be an object")
    sources = mgmt.get("sources") or []
    if not isinstance(sources, list):
        die("policy: management.sources must be a list")
    mport = port(mgmt.get("port", 22), "management.port")
    mproto = str(mgmt.get("proto", "tcp")).lower()
    if mproto not in ("tcp", "udp"):
        die("management.proto must be tcp or udp: %s" % mproto)

    cut_raw = pol.get("cut") or DEFAULT_CUT
    if not isinstance(cut_raw, list):
        die("policy: cut must be a list of CIDRs")
    cut = [net4(c, "cut") for c in cut_raw]
    if not cut:
        die("policy: cut is empty, nothing to isolate")

    keep = pol.get("keep_egress") or []
    if not isinstance(keep, list):
        die("policy: keep_egress must be a list")
    egress = []
    for item in keep:
        if not isinstance(item, dict):
            die("keep_egress entries must be objects")
        proto = str(item.get("proto", "tcp")).lower()
        if proto not in ("tcp", "udp"):
            die("keep_egress.proto must be tcp or udp: %s" % proto)
        egress.append((net4(item.get("to"), "keep_egress.to"), proto,
                       port(item.get("port"), "keep_egress.port")))

    if not sources:
        print("REFUSED no management.sources in the policy")
        print("FINDING a ruleset without a management accept cuts the console")
        sys.exit(1)

    net_sources = [net4(src, "management.sources") for src in sources]
    print("PLAN quarantine %s %s%s" % (args.host, ip,
                                       " (iptables)" if args.iptables else ""))
    for src in net_sources:
        print("KEEP mgmt %s %s/%d" % (src, mproto, mport))
    for to, proto, p in egress:
        print("KEEP egress %s %s/%d" % (to, proto, p))
    print("CUT %s" % " ".join(str(c) for c in cut))

    if args.iptables:
        rules = [
            "iptables -I INPUT 1 -i lo -j ACCEPT",
            "iptables -I INPUT 2 -m conntrack "
            "--ctstate ESTABLISHED,RELATED -j ACCEPT",
        ]
        for i, src in enumerate(net_sources, start=3):
            rules.append("iptables -I INPUT %d -s %s -p %s --dport %d "
                         "-j ACCEPT" % (i, src, mproto, mport))
        pos = len(rules) + 1
        for c in cut:
            rules.append("iptables -I INPUT %d -s %s -j DROP" % (pos, c))
            pos += 1
        rules.append("iptables -P INPUT DROP")
        rules.append("iptables -I OUTPUT 1 -o lo -j ACCEPT")
        rules.append("iptables -I OUTPUT 2 -m conntrack "
                     "--ctstate ESTABLISHED,RELATED -j ACCEPT")
        opos = 3
        for to, proto, p in egress:
            rules.append("iptables -I OUTPUT %d -d %s -p %s --dport %d "
                         "-j ACCEPT" % (opos, to, proto, p))
            opos += 1
        for c in cut:
            rules.append("iptables -I OUTPUT %d -d %s -j DROP" % (opos, c))
            opos += 1
        rules.append("iptables -P OUTPUT DROP")
        text = "#!/bin/sh\n# quarantine %s, generated by quarantine_plan.py\n" \
               "set -eu\n%s\n" % (args.host, "\n".join(rules))
        loader = "sh"
        suffix = ".sh"
    else:
        in_rules = ["iif lo accept", "ct state established,related accept"]
        for src in net_sources:
            in_rules.append("ip saddr %s %s dport %d accept"
                            % (src, mproto, mport))
        in_rules.append("ip saddr { %s } drop"
                        % ", ".join(str(c) for c in cut))
        out_rules = ["oif lo accept", "ct state established,related accept"]
        for to, proto, p in egress:
            out_rules.append("ip daddr %s %s dport %d accept" % (to, proto, p))
        out_rules.append("ip daddr { %s } drop"
                         % ", ".join(str(c) for c in cut))
        rules = in_rules + out_rules
        text = (
            "table inet %s {\n"
            "    chain input {\n"
            "        type filter hook input priority 0; policy drop;\n"
            "        %s\n"
            "    }\n"
            "    chain output {\n"
            "        type filter hook output priority 0; policy drop;\n"
            "        %s\n"
            "    }\n"
            "}\n" % (table, "\n        ".join(in_rules),
                     "\n        ".join(out_rules)))
        loader = "nft -f"
        suffix = ".nft"

    for i, rule in enumerate(rules, start=1):
        print("RULE %d %s" % (i, rule))
    print("READY %d rules, management path first" % len(rules))

    if not args.apply:
        print("DRY-RUN nothing written. Add --apply to write the ruleset.")
        return 0

    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", args.host)
    out = args.out or ("/tmp/quarantine-%s%s" % (safe, suffix))
    try:
        fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(out, 0o600)
    except OSError as exc:
        die("%s: %s" % (out, exc.strerror or exc))
    print("WROTE %s mode 0600" % out)
    print("APPLY %s %s" % (loader, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
