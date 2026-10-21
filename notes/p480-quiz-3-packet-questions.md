---
id: p480
title: "Quiz: 3 packet questions"
slug: quiz-3-packet-questions
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, SRE, DevOps, HTTP, CloudNative]
source: "LinkedIn post P480 · Network series"
linkedin_date: 2029-10-21
design: quiz
---

# Quiz: 3 packet questions

Three questions come up in every network review, and the answers are more mechanical than most people expect.

## Quick reference

**Q1. Why does TIME_WAIT exist?**

- a) To retransmit the request body
- b) To absorb delayed duplicates
- c) To reserve the port for ever

> **Answer:** b) To absorb delayed duplicates. The active closer waits twice the maximum segment lifetime so delayed duplicates from the old connection expire, and a lost final ACK can be retransmitted.

**Q2. A load balancer returns 502. What usually happened?**

- a) The upstream refused or reset
- b) The upstream was too slow
- c) The client sent a bad header

> **Answer:** a) The upstream refused or reset. 502 means the balancer could not get a valid response: connection refused, reset or malformed. 504 is the slow one, where the upstream was reachable but timed out.

**Q3. Why does keep-alive cut latency?**

- a) It compresses each request
- b) It skips TCP and TLS setup
- c) It caches the response

> **Answer:** b) It skips TCP and TLS setup. Reusing a connection avoids a new TCP handshake and TLS handshake, and keeps slow start warm. On HTTP/2 the same connection also carries many streams.

## Explained

### Why TIME_WAIT

Question one: why does TIME_WAIT exist? The side that closes first waits twice the maximum segment lifetime before the tuple can be reused. That wait does two jobs: it lets a delayed duplicate segment from the old connection expire, and it lets the final ACK be retransmitted if the peer never received it. Without it, a new connection on the same port pair could receive a stale packet. It is not a leak.

### What a 502 means

Question two: a load balancer returns 502. Usually the balancer could not get a valid response from the upstream: the connection was refused, reset, or the reply was malformed. The application may have crashed, the port may be wrong, or the upstream may have closed the connection early. A 504 is different: the upstream was reachable but too slow, and the balancer gave up waiting.

### Why keep-alive helps

Question three: why does keep-alive cut latency? A fresh HTTPS request pays a TCP handshake and a TLS handshake before the first byte of the request. Reusing the connection skips the handshakes and the slow start that follows them, so the second request leaves immediately. On HTTP/2, one connection also carries many concurrent streams.

> **The honest caveat:** 502 is a symptom, not a cause. The balancer log names the upstream, and that upstream's log names the real error.

> **The lesson:** the packet state and the status code are evidence, not opinion.

## In one line

> **The packet tells you the answer.** Three questions worth asking before the next incident.

**Ask the kernel**

```bash
ss -s
```
