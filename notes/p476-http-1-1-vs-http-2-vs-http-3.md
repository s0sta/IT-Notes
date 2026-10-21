---
id: p476
title: "HTTP/1.1 vs HTTP/2 vs HTTP/3"
slug: http-1-1-vs-http-2-vs-http-3
sections: [it, devsecops]
topic: "Web servers, TLS & HTTP"
tags: [HTTP, Networking, Performance, WebPerformance, DevOps]
source: "LinkedIn post P476 · Network series"
linkedin_date: 2029-10-11
design: matrix
---

# HTTP/1.1 vs HTTP/2 vs HTTP/3

Three versions of HTTP carry the same request, and the difference is not the syntax. It is what one lost packet does to everything else sharing the connection.

## Quick reference

| | **HTTP/1.1** | **HTTP/2** | **HTTP/3** |
|:--|:--|:--|:--|
| Transport | TCP | TCP | QUIC over UDP |
| Multiplexing | No, six connections | Streams over one TCP | Streams over QUIC |
| Head-of-line | Blocks the next | TCP loss stalls all | Stalls one stream |
| Handshake | TCP + TLS, 2-3 RTT | TCP + TLS 1.3, 2 RTT | QUIC, 1 RTT or 0 |
| Server push | No | Yes, but rarely used | Not in HTTP/3 |
| Best for | Legacy and simple | Busy sites on TCP | Lossy mobile links |

**How to pick**

- **HTTP/1.1** → legacy clients and simple paths.
- **HTTP/2** → many requests on a reliable network.
- **HTTP/3** → mobile, lossy and high-latency links.

## Explained

### Transport

HTTP/1.1 and HTTP/2 both run over TCP. HTTP/3 runs over QUIC, which is built on UDP and implements its own streams, loss detection and encryption. UDP is not a downgrade here; it is the layer QUIC needs to avoid TCP's ordering.

### Multiplexing

HTTP/1.1 handles one response at a time per connection, so browsers open about six. HTTP/2 puts many streams on one TCP connection, each with its own identifier. HTTP/3 keeps the streams but moves them onto QUIC, where they are independent by design.

### Head-of-line

HTTP/1.1 blocks the next response behind the current one. HTTP/2 removes the application-level queue but keeps the TCP one: a single lost segment stalls every stream until it is retransmitted. HTTP/3 stalls only the stream that lost the packet, which is why it wins on mobile and lossy links.

### Handshake, push, fit

HTTP/1.1 costs a TCP handshake plus TLS. HTTP/2 pays the same two handshakes, though TLS 1.3 cuts one round trip. HTTP/3 folds transport and crypto into one QUIC handshake, with 0-RTT resumption. Server push exists in HTTP/2 and is rarely used; HTTP/3 has no push. HTTP/1.1 suits legacy clients, HTTP/2 busy sites on reliable networks, HTTP/3 lossy mobile paths.

> **The honest caveat:** HTTP/3 needs UDP 443 open end to end, and some corporate networks still block it, so a working HTTP/2 path is not wasted.

> **The lesson:** framing decides what one lost packet costs.

## In one line

> **Framing decides what stalls.** The version matters less than what one lost packet blocks.

**See the version**

```bash
curl -sI https://example.com | head -1
```
