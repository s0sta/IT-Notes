---
id: p127
title: "Subnet sizes cheat sheet"
slug: subnet-sizes-cheat-sheet
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, CCNA, Subnetting, ITSupport, ITInfrastructure]
source: "LinkedIn post P127 · Linux + IT series"
linkedin_date: 2027-07-20
design: numbers
---

# Subnet sizes cheat sheet

Six subnet sizes worth knowing by heart. They come up in network design, firewall rules, cloud VPCs and almost every networking interview.

## Quick reference

| Number | What | Why it matters | |
|:--|:--|:--|:--|
| **254** | /24  255.255.255.0 | The classic office or home network. | /24 |
| **126** | /25  255.255.255.128 | Half a /24. Two departments from one range. | /25 |
| **62** | /26  255.255.255.192 | A floor, a branch, or a server VLAN. | /26 |
| **30** | /27  255.255.255.224 | A small team, printers, or cameras. | /27 |
| **14** | /28  255.255.255.240 | A few servers or a DMZ. | /28 |
| **2** | /30  255.255.255.252 | A link between two routers. | /30 |

## Explained

254 usable hosts, a /24, mask 255.255.255.0. The classic office or home network, like 192.168.1.0/24. 256 addresses minus the network address and the broadcast address.

126 usable hosts, a /25, mask 255.255.255.128. Half of a /24. One /24 split into two networks, for example staff and printers.

62 usable hosts, a /26, mask 255.255.255.192. A good size for one floor, a small branch, or a server VLAN.

30 usable hosts, a /27, mask 255.255.255.224. A small team, a group of printers, or security cameras in their own segment.

14 usable hosts, a /28, mask 255.255.255.240. A handful of servers or a DMZ. Cloud providers often reserve a few extra addresses in every subnet, so check before you size tightly.

2 usable hosts, a /30, mask 255.255.255.252. Traditionally used for the link between two routers. A /31 is also allowed for point-to-point links and saves two addresses.

> **The pattern that makes it easy:** every extra bit in the prefix halves the number of addresses, and you subtract two for the network and broadcast addresses.

usable hosts = 2^(32 - prefix) - 2.

Size subnets for growth. Renumbering a full network later is far harder than leaving room now.

## In one line

> **Each bit halves it. Minus two.** Network address and broadcast are not usable.

**The formula:** usable = 2^(32 - prefix) - 2
