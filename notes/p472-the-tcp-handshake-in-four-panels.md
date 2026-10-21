---
id: p472
title: "The TCP handshake in four panels"
slug: the-tcp-handshake-in-four-panels
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [TCP, Networking, DevOps, SRE, CloudNative]
source: "LinkedIn post P472 · Network series"
linkedin_date: 2029-10-02
design: explainer
---

# The TCP handshake in four panels

A browser opens a connection and the first byte waits while three small packets cross the network. The handshake is the part of TCP nobody draws, and it decides how long every later request takes.

## Quick reference

### 1. SYN

- Picks an initial sequence number (ISN)
- Offers MSS, window scale and SACK
- No payload: the packet is a proposal

### 2. SYN-ACK

- Server picks its own ISN
- Acknowledges client ISN plus one
- Returns its own options in the same packet

### 3. ACK

- Acknowledges server ISN plus one
- Both directions are now established
- This ACK may already carry request data

### 4. Data

- Sequence numbers count bytes, not packets
- Acknowledgements are cumulative
- One round trip spent before the URL leaves

> **Note:** Three packets, one round trip, then the request can leave.

## Explained

### Four panels

SYN. The client picks an initial sequence number, sets the SYN flag and offers its options: maximum segment size, window scale and selective ACK. There is no payload yet. The packet is a proposal, not a connection.

SYN-ACK. The server picks its own initial sequence number, acknowledges the client's sequence number plus one, and returns its own options. Both sides now know the other is reachable and what each can send.

ACK. The client acknowledges the server's ISN plus one. The connection is established in both directions, and this ACK may already carry data.

Data. Sequence numbers count bytes, not packets, and acknowledgements are cumulative: each one names the next byte the sender expects. A retransmission fills a gap instead of repeating the whole stream.

### What it costs

The handshake spends one full round trip before the request can leave, and TLS adds its own round trips on top. On a 40 ms link that is 40 ms of pure waiting for every new connection, before the server has seen a URL.

> **The honest caveat:** TCP Fast Open can put data in the SYN, but middleboxes still drop it often enough that the first round trip remains the norm.

> **The lesson:** count the round trips before you blame the server.

## In one line

> **One round trip before the request.** The first byte you send is not the first packet on the wire.

**Count the rtt**

```bash
curl -w '%{time_connect}' -sI URL
```
