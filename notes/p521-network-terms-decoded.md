---
id: p521
title: "Network terms, decoded"
slug: network-terms-decoded
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, TCP, SRE, Observability, Engineering]
source: "LinkedIn post P521 · Network series"
linkedin_date: 2030-01-24
design: reveal
---

# Network terms, decoded

Six words get used in every network incident, and two of them are usually being defined differently by the people in the room.

## Quick reference

- **RTT** — A packet there and back. Ping measures it; half is one-way only on a symmetric path.
- **BDP** — Bandwidth times RTT divided by 8: the bytes in flight needed to fill the pipe.
- **MTU** — The largest payload one frame carries. Ethernet defaults to 1500 bytes.
- **Anycast** — One IP announced from many places; BGP usually picks the nearest, so the path can change.
- **Overlay** — A network built on another. VXLAN wraps frames in UDP and adds 50 bytes.
- **Retransmit** — A segment sent again because no ACK arrived; it rises before latency does.

## Explained

### Path

RTT is the round-trip time: a packet there and back. Ping measures it, and half of it is the one-way latency only when the path is symmetric. BDP is bandwidth times RTT divided by 8, the bytes that must be in flight to fill the pipe; at 1 Gbps and 40 ms it is 5 MB.

### Frames

MTU is the largest payload one frame carries; Ethernet defaults to 1500 bytes, and every tunnel header comes out of that budget. Anycast is one IP address announced from many places, so BGP usually picks the nearest and the path can change without the address changing.

### Hidden layers

Overlay is a network built on another: VXLAN wraps the frame in UDP, adds 50 bytes, and hides the underlay from the workload. Retransmit is a segment sent again because no ACK arrived, a counter that rises before latency does.

> **The honest caveat:** a definition is not a measurement. Two teams can agree on RTT and still quote different numbers, because one timed a ping and the other timed a request.

> **The lesson:** a network you can describe is a network you can debug.

That is the series. Fifty posts, from the first handshake to a network you can operate, five phases and ten Python scripts. Thank you for following along.

## In one line

> **Name the term, measure the path.** A network you can describe is a network you can debug.

**Count the hops**

```bash
mtr -rw api.example.com
```
