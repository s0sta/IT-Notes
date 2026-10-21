---
id: p478
title: "Anatomy of a connection tuple"
slug: anatomy-of-a-connection-tuple
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [TCP, Networking, Linux, SysAdmin, SRE]
source: "LinkedIn post P478 · Network series"
linkedin_date: 2029-10-16
design: anatomy
---

# Anatomy of a connection tuple

A server sees 10.0.4.7:49152 connect to 10.0.8.20:443, and those addresses and ports are the connection.

## Quick reference

```text
10.0.4.7:49152 -> 10.0.8.20:443
```

| Part | Name | What it means |
|:--|:--|:--|
| `10.0.4.7` | Source IP | The client. Private in the VPC, NATed before it reaches the internet. |
| `:49152` | Source port | Ephemeral, chosen per connection. The half that makes the tuple unique. |
| `->` | The arrow | Direction of the first packet. Every reply reverses it. |
| `10.0.8.20` | Destination IP | The server the client resolved. Anycast may land on another machine. |
| `:443` | Destination port | 443 means TLS. The listener that accepts the connection. |

## Explained

### The tuple

Source IP. 10.0.4.7 is the client. It is private in the VPC. The server routes its reply here, so changing it changes the return path.

Source port. 49152 is the ephemeral port. The client picks it from the kernel's range, usually 32768 to 60999 on Linux, to tell this connection from every other to the same server. Two connections to one host get two source ports.

The arrow. The arrow is direction, not a field. The first packet travels from source to destination, and every reply reverses the addresses and ports. A stateful firewall remembers the direction, so the reply needs no rule.

Destination IP. 10.0.8.20 is the server. The client got it from DNS, and with anycast it may not be the machine that runs the code.

Destination port. 443 is the listener. It tells the server which service receives the packet, and it rarely changes between connections.

### What NAT does

NAT rewrites the source address and port on the way out and keeps the mapping, so the reply finds its way back. The server sees the NAT address, not 10.0.4.7, which is why a connection can look healthy on the client and unknown on the server.

> **The honest caveat:** the real key is a five-tuple, and the drawing leaves out the protocol. TCP and UDP can share the same addresses and ports.

> **The lesson:** a connection is an address pair and a port pair, and NAT rewrites half of it.

## In one line

> **The tuple is the connection.** Change one field and it is a different connection.

**See your tuples**

```bash
ss -tanp
```
