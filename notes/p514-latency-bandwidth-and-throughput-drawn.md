---
id: p514
title: "Latency, bandwidth and throughput, drawn"
slug: latency-bandwidth-and-throughput-drawn
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, Latency, Performance, SRE, DevOps]
source: "LinkedIn post P514 · Network series"
linkedin_date: 2030-01-08
design: explainer
---

# Latency, bandwidth and throughput, drawn

A 1 Gbps link and a 100 ms round trip can feel slower than a home connection, and the reason is arithmetic, not hardware.

## Quick reference

### Round-trip time (RTT)

- One packet there and back
- TCP handshake: one RTT
- TLS 1.3: one more RTT
- Add one for the request

### Bandwidth

- Capacity of the narrowest link
- Bits per second, not seconds
- A wider pipe does not shorten RTT

### Throughput

- What actually arrives
- Window divided by RTT
- 64 KB at 100 ms is about 5 Mbps

### The bottleneck

- The slowest hop wins
- Look for queues and firewalls
- Loss makes the window smaller

> **Note:** Latency and bandwidth are different budgets; a bigger pipe does not shorten the path.

## Explained

### Round trip

RTT is the time a packet takes to go and come back. Ping reports it in milliseconds; the path holds two one-way trips, and only a symmetric path makes each half the RTT. A TCP handshake costs one RTT before data, TLS 1.3 costs another, and the request itself costs a third.

### Bandwidth

Bandwidth is the pipe's capacity in bits per second. It belongs to the narrowest link, not to the server, and it says nothing about delay. Upgrading a circuit raises the ceiling without moving the floor.

### Throughput

Throughput is what arrives. With a 64 KB window and a 100 ms RTT, the sender can have 64 KB in flight, so throughput is 64 KB divided by 0.1 seconds, about 5 Mbps, however fast the link claims to be.

### The bottleneck

The bottleneck is the slowest hop, and it is not always the one with the least bandwidth. A stateful firewall, a saturated queue or a resolver answering slowly can set the pace for a path with capacity to spare.

> **The honest caveat:** ping measures ICMP, which some routers deprioritise; time a TCP handshake to the port your users actually call.

> **The lesson:** latency and bandwidth are separate budgets, and you spend both.

## In one line

> **Distance sets the floor.** You can buy bandwidth; you cannot buy a shorter round trip.

**Measure the rtt**

```bash
ping -c 5 api.example.com
```
