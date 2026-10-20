---
id: p131
title: "How your data is wrapped to cross the network (TCP/IP)"
slug: how-your-data-is-wrapped-to-cross-the-network-tcp-ip
sections: [it]
topic: "Networking & DNS"
tags: [Networking, CCNA, TCPIP, SysAdmin, ITInfrastructure]
source: "LinkedIn post P131 · Linux + IT series"
linkedin_date: 2027-07-29
design: stack
---

# How your data is wrapped to cross the network (TCP/IP)

When you load a web page, your data does not travel as-is. Each layer of the TCP/IP stack wraps it in another header on the way out, and the receiver unwraps it in reverse. Understanding this explains most networking tools and most networking problems.

## Quick reference

*Top to bottom: each layer adds a header*

1. **Application** — Your actual data: an HTTP request, an email, a query. · `HTTP / DNS`
2. **Transport** — Adds a TCP or UDP header with port numbers. · `TCP :443`
3. **Internet** — Adds an IP header with source and destination IPs. · *IP addresses*
4. **Link** — Wraps it in a frame with source and destination MACs. · `Ethernet / MAC`
5. **Physical** — The frame becomes signals on copper, fibre or radio. · *bits on the wire*

## Explained

Application. Your actual data: an HTTP request for a page, a DNS query, an email. At this point it is just the message your program wants to send.

Transport. A TCP or UDP header is added. It carries the source and destination port numbers, so the receiving machine knows which program the data is for: 443 for HTTPS, 53 for DNS. TCP also adds sequence numbers so lost pieces can be resent.

Internet. An IP header is added, with the source and destination IP addresses. This is what routers read to move the packet across networks toward its destination. TTL lives here, which is how traceroute works.

Link. The packet is wrapped in a frame with source and destination MAC addresses, for the next hop on the local network. Unlike the IP address, the MAC changes at every hop. ARP is how a device finds the MAC for an IP.

Physical. The frame becomes actual signals: electricity on copper, light on fibre, or radio on Wi-Fi.

Why it matters in practice: a firewall port rule works at the transport layer, routing works at the internet layer, a switch and ARP work at the link layer, and a dead cable is physical. Knowing which layer your problem is on tells you which tool to reach for.

`sudo tcpdump -n -i any port 443` lets you watch these headers on a real connection.

## In one line

> **Every layer adds, then removes, a header.** The receiver unwraps it in the exact reverse order.

**Watch it happen**

```bash
sudo tcpdump -n -i any port 443
```
