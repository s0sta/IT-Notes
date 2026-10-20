---
id: p276
title: "The OSI model, grouped"
slug: the-osi-model-grouped
sections: [it]
topic: "Networking & DNS"
tags: [Networking, OSI, CCNA, ITInfrastructure, DevOps]
source: "LinkedIn post P276 · Visual series"
linkedin_date: 2028-07-02
design: explainer
---

# The OSI model, grouped

A request fails and three people blame three layers: the cable, the firewall, the application. The OSI model is not academic; it is a way to split that argument into seven testable questions.

## Quick reference

### Layers 1-2 - Link

- Cable, Wi-Fi, MAC addresses, frames
- Switches forward by MAC, not by IP
- Ethernet, ARP, VLANs and PPP
- Everything above assumes it works

### Layer 3 - Network

- IP addresses, packets, routing
- A router chooses the next hop
- ICMP, ping and traceroute
- NAT and IPsec sit here too

### Layer 4 - Transport

- TCP and UDP, ports and segments
- TCP numbers bytes, re-sends loss
- UDP sends datagrams, keeps no state
- Firewalls filter ports at layer 4

### Layers 5-7 - Session and up

- Session: starts and ends the conversation
- Presentation: TLS, compression, encoding
- Application: HTTP, DNS, SMTP, SSH
- Most tickets land in this group

> **Note:** TCP/IP uses four layers: link, internet, transport, application.

## Explained

### Link and network

The first two layers are the link: cable, Wi-Fi, MAC addresses and frames. A switch forwards by MAC, not by IP. Ethernet, ARP, VLANs and PPP live here, and everything above assumes this works. Layer 3 is the network: IP addresses, packets and routing. A router chooses the next hop, ICMP and traceroute report the path, and NAT and IPsec rewrite or protect packets here.

### Transport and above

Layer 4 is transport: TCP and UDP, ports and segments. TCP numbers bytes and re-sends what is lost; UDP sends datagrams and keeps no state. Firewalls filter ports here. Layers 5 to 7 are the upper group: session starts and ends the conversation, presentation handles TLS, compression and encoding, application is HTTP, DNS, SMTP and SSH. Most tickets land in this group.

### How to use it

Start low. If ping fails, the problem is layer 3 or below. If ping works and the port refuses, it is layer 4. If the port answers and the page is wrong, it is layer 7. The panel order in the drawing is the order you test.

> **The honest caveat:** this is a teaching model, not an implementation; TLS is drawn at layer 6 by some people and between layers 4 and 7 by others.

> **The lesson:** name the layer before you name the culprit.

## In one line

> **Know the layer, know the suspect.** The layer that failed narrows the tool you reach for.

**Name the layer**

```bash
ping, dig, curl -v, ss -tlnp
```
