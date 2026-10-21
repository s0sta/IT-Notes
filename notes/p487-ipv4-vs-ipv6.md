---
id: p487
title: "IPv4 vs IPv6"
slug: ipv4-vs-ipv6
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [IPv4, IPv6, Networking, DNS, DevOps]
source: "LinkedIn post P487 · Network series"
linkedin_date: 2029-11-06
design: compare
---

# IPv4 vs IPv6

A new service gets an AAAA record and half the office cannot reach it. The other half cannot reach the A record. The two protocols are not two versions of the same address; they are two address spaces.

## Quick reference

| | **IPV4** | **IPV6** |
|:--|:--|:--|
| Address size | 32 bits, 4 octets | 128 bits, 16 octets |
| Written as | 203.0.113.10 | 2001:db8::10 |
| DNS record | A | AAAA |
| Configuration | DHCP or manual | SLAAC, DHCPv6 optional |
| NAT | Common, address shortage | Rare, no shortage |
| Discovery | ARP and broadcast | NDP and multicast |

**IPV4** (32-bit dotted quad): Four bytes, four decimal octets, and most of the internet.

```bash
dig example.com A +short
```

**IPV6** (128-bit hex groups): Sixteen bytes, eight hex groups, and :: for a run of zeros.

```bash
dig example.com AAAA +short
```

- IPv4 → everywhere, and out of addresses.
- IPv6 → the same internet, with room.

## Explained

### Size and notation

IPv4 is 32 bits, written as four decimal octets such as 203.0.113.10. IPv6 is 128 bits, written as eight groups of four hex digits, with :: allowed once for a run of zeros, as in 2001:db8::10.

### DNS and configuration

An A record holds an IPv4 address and an AAAA record holds an IPv6 one. IPv4 hosts get an address from DHCP or a static file; IPv6 hosts usually build one from a router advertisement with SLAAC, and DHCPv6 is optional.

### NAT and discovery

IPv4 often sits behind NAT because the address space ran out, so many hosts share one public address. IPv6 has enough addresses that NAT is rare, though NPTv6 exists for translation. IPv4 finds neighbours with ARP and broadcast; IPv6 uses Neighbour Discovery over multicast, with no broadcast at all. The two run side by side on one host, and a client with a working IPv6 path will usually try it first.

> **The honest caveat:** dual stack is the normal deployment, not a migration deadline, and an IPv6 path is not automatically faster; it is a different path that has to be measured.

> **The lesson:** choose the record by what the client can reach, not by what the RFC prefers.

Two protocols,  
one address space.
