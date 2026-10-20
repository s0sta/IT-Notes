---
id: p279
title: "TCP vs UDP"
slug: tcp-vs-udp
sections: [it]
topic: "Networking & DNS"
tags: [Networking, TCP, UDP, DevOps, SRE]
source: "LinkedIn post P279 · Visual series"
linkedin_date: 2028-07-09
design: compare
---

# TCP vs UDP

A video call freezes for half a second and the SSH session stays perfect. Both crossed the same network; the difference is what each transport promised before the first packet.

## Quick reference

| | **TCP** | **UDP** |
|:--|:--|:--|
| Handshake | 3-way SYN, SYN-ACK, ACK | None |
| Delivery | Acknowledged, re-sent | Best effort, dropped |
| Order | Sequence numbers | Whatever arrives |
| Header | 20 bytes minimum | 8 bytes fixed |
| Speed | Slower: round trips | Faster: no setup |
| Best for | Web, SSH, file transfer | DNS, video, games, VoIP |

**TCP** (Reliable, ordered byte stream): Handshake, order, sequence numbers, retransmission.

```bash
ss -tan state established
```

**UDP** (Connectionless datagrams): No handshake, no order, no retransmission.

```bash
dig +notcp example.com
```

- TCP → reliable and ordered, at the cost of round trips.
- UDP → no promises, no waiting, lower latency.

## Explained

### Handshake and delivery

TCP opens with a three-way handshake: SYN, SYN-ACK, ACK. That is one round trip before data, which is why a new TCP connection feels slower. UDP has no handshake and no connection. TCP then acknowledges what arrives and re-sends what does not; UDP sends each datagram and forgets it.

### Order, header, speed

TCP numbers the bytes, so the application reads an ordered stream even when packets arrive out of order. UDP preserves no order at all. A TCP header is at least 20 bytes before options; a UDP header is 8. TCP pays for its guarantees in round trips and state, so it is slower to start; UDP has no setup and no state, so it starts immediately.

### Where each fits

TCP is the default for web, SSH and file transfer, where every byte matters. UDP is the default for DNS, video, games and VoIP, where a late packet is worse than a missing one.

> **The honest caveat:** the boundary is a default, not a law. DNS falls back to TCP when a reply is truncated, and QUIC puts reliability and ordering back on top of UDP.

> **The lesson:** choose the promise you need, then pay for it.

TCP waits for proof. UDP sends and moves on.
