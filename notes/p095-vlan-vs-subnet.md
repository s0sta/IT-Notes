---
id: p95
title: "VLAN vs Subnet"
slug: vlan-vs-subnet
sections: [it]
topic: "Networking & DNS"
tags: [Networking, CCNA, VLAN, ITInfrastructure, NetworkSecurity]
source: "LinkedIn post P95 · Linux + IT series"
linkedin_date: 2027-05-06
design: compare
---

# VLAN vs Subnet

VLANs and subnets are often mixed up because they are almost always used together. They solve the problem at two different layers.

## Quick reference

| | **VLAN** | **SUBNET** |
|:--|:--|:--|
| OSI layer | Layer 2 (data link) | Layer 3 (network) |
| Configured on | Switches, 802.1Q tags | IP addresses and masks |
| Separates | Broadcast domains | IP networks |
| Talk across | Router or L3 switch | Router or L3 switch |
| Example | VLAN 20 = Finance | 192.168.20.0/24 |
| Usual design | One subnet per VLAN | One VLAN per subnet |

**VLAN** (Layer 2 separation): Splits one physical switch into separate broadcast domains.

Example: `switchport access vlan 20`

**SUBNET** (Layer 3 addressing): Splits an IP range into networks that need a router to talk.

Example: `192.168.20.0/24`

- VLAN → separates devices on the switch.
- Subnet → separates addresses in IP. Use them together.

## Explained

A VLAN works at Layer 2, on the switch. switchport access vlan 20 puts a port into VLAN 20. Devices in VLAN 20 can only see each other's broadcasts, as if they were on a separate physical switch. Between switches, a trunk carries many VLANs over one cable, with an 802.1Q tag on each frame saying which VLAN it belongs to.

A subnet works at Layer 3, in IP addressing. 192.168.20.0/24 is a range of 254 usable addresses. Devices in different subnets cannot talk directly. Their traffic has to go through a router or a Layer 3 switch.

### How they fit together

The usual design is one subnet per VLAN. VLAN 10 is 192.168.10.0/24 for staff, VLAN 20 is 192.168.20.0/24 for finance, VLAN 30 for printers, VLAN 40 for guest Wi-Fi. The router or Layer 3 switch has an interface in each one, and that is where you control what can talk to what.

### Where people get confused

Putting two subnets in one VLAN works, but broadcasts still reach everyone, so you gain addresses, not separation.  
Creating VLANs without firewall rules between them separates broadcasts, but the router may still forward everything. The security comes from the rules on the router, not from the VLAN alone.

The practical win: printers, cameras and guest devices in their own VLAN and subnet means a compromised camera cannot reach the finance PCs.

VLAN separates on the switch. Subnet separates in IP. Use both.
