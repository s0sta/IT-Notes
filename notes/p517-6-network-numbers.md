---
id: p517
title: "6 network numbers"
slug: 6-network-numbers
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, Latency, TCP, SRE, Performance]
source: "LinkedIn post P517 · Network series"
linkedin_date: 2030-01-15
design: numbers
---

# 6 network numbers

Six numbers explain most of the tickets that arrive as "it is slow". None of them is a speed test.

## Quick reference

| Number | What | Why it matters | |
|:--|:--|:--|:--|
| **1500** | Ethernet MTU | The payload a standard frame carries; 1460 is TCP's MSS. | mtu |
| **1 RTT** | TCP handshake | SYN, SYN-ACK, ACK before data; the third leg can carry it. | tcp |
| **1 RTT** | TLS 1.3 handshake | One round trip after TCP, so the first byte waits two. | tls |
| **5 MB** | BDP at 1 Gbps, 40 ms | Bandwidth x RTT / 8: the data in flight to fill the pipe. | bdp |
| **150 ms** | Cross-region RTT | Same continent 10-40 ms; across an ocean 150-250 ms. | rtt |
| **1%** | Packet loss | Enough to cut a 40 ms path to single-digit Mbps. | loss |

## Explained

### Size

1500 bytes is the Ethernet MTU, the payload a standard frame carries, and 1460 is what TCP gets after 20 bytes of IP and 20 of TCP header. Jumbo frames push the MTU to 9000 on a controlled LAN, and every hop must agree or the path falls back to 1500.

### Round trips

A TCP handshake costs 1 RTT before data, and TLS 1.3 costs 1 more, so the first byte waits 2 RTT and the request waits a third.

### The pipe

The BDP at 1 Gbps and 40 ms is 5 MB, the data in flight needed to fill the link. A 64 KB window there allows about 13 Mbps, which is why a long path with a small window looks like a slow link.

### Distance and loss

Cross-region RTT is 150 ms across an ocean, against 10-40 ms on the same continent, so three round trips cost 450 ms before the server has done any work. A 1% packet loss can pull a 40 ms path into single-digit Mbps, because TCP reads loss as congestion and cuts the window.

> **The honest caveat:** these are round numbers from textbook paths. Real RTT depends on routing, peering and queueing, and your 150 ms may be 90 on a good day.

> **The lesson:** put a number on the path before you blame the application.

## In one line

> **Distance costs round trips.** Every handshake, window and retransmit is paid in RTT.

**Measure one path**

```bash
mtr -rw api.example.com
```
