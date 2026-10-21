---
id: p473
title: "The network debugging cheat sheet"
slug: the-network-debugging-cheat-sheet
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, Troubleshooting, Linux, DevOps, SRE]
source: "LinkedIn post P473 · Network series"
linkedin_date: 2029-10-04
design: cheatsheet
---

# The network debugging cheat sheet

A request fails and everyone has an opinion: DNS, the firewall, the certificate, the server. Four blocks of commands settle it in the order the packet travels.

## Quick reference

### DNS

```bash
dig example.com +short
dig example.com @1.1.1.1 +short
dig +trace example.com
dig -x 10.0.0.5 +short
```

### Reach

```bash
ping -c 4 10.0.8.20
traceroute -n 10.0.8.20
nc -vz 10.0.8.20 443
curl -sS -I https://example.com
```

### Sockets

```bash
ss -tlnp
ss -tan state established
ss -s
ss -tanp | grep 10.0.8.20
```

### Capture

```bash
tcpdump -i any port 443 -nn
tcpdump -nn port 53
tcpdump -i eth0 -w /tmp/cap.pcap
tcpdump -r /tmp/cap.pcap -nn
```

## Explained

### DNS

Start with the name. `dig example.com +short` returns the address your resolver would use. `dig example.com @1.1.1.1 +short` asks a different resolver, which separates a local problem from a global one. `dig +trace example.com` walks down from the root. `dig -x 10.0.0.5 +short` reverses an address you found in a log.

### Reach

Then the path. `ping -c 4 10.0.8.20` proves the host answers ICMP, though many firewalls block it, so a timeout is not proof of death. `traceroute -n 10.0.8.20` shows the hops. `nc -vz 10.0.8.20 443` tests one port. `curl -sS -I https://example.com` proves the service answers at the application layer.

### Sockets

On the host, `ss -tlnp` shows what is listening and which process owns it. `ss -tan state established` shows live connections. `ss -s` gives the summary when the table is too long. `ss -tanp | grep 10.0.8.20` finds every socket talking to one peer.

### Capture

When the counters disagree with the story, capture. `tcpdump -i any port 443 -nn` shows the packets. `tcpdump -nn port 53` catches DNS. `tcpdump -i eth0 -w /tmp/cap.pcap` writes a file, and `tcpdump -r /tmp/cap.pcap -nn` reads it back later.

> **The honest caveat:** a capture on one host cannot see packets dropped by a middlebox, and tcpdump needs root or the right capability.

> **The lesson:** test the layers in order, and stop at the first one that disagrees.

## In one line

> **Follow the packet, not the guess.** The answer is in the path, not in the ticket.

**Capture one flow**

```bash
tcpdump -nn -i any port 443
```
