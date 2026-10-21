---
id: p481
title: "5 network mistakes"
slug: 5-network-mistakes
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, DevOps, SRE, CloudNative, Troubleshooting]
source: "LinkedIn post P481 · Network series"
linkedin_date: 2029-10-23
design: dontdo
---

# 5 network mistakes

A network fails at the defaults, not the clever parts. These five turn a blip into an outage.

## Quick reference

**1.** ❌ **No timeout on a request** — A hung peer holds workers until the pool is empty.  
✅ **Connect and read timeouts** — Fail fast and keep capacity for healthy peers.

**2.** ❌ **A new connection per call** — Every call pays TCP and TLS before the first byte.  
✅ **Pool with keep-alive** — One handshake serves hundreds of requests.

**3.** ❌ **MTU set too small** — More packets, more headers, and UDP gets fragmented.  
✅ **Match the smallest link MTU** — Usually 1500 on the internet; jumbo stays inside.

**4.** ❌ **Retry immediately, ten times** — A struggling service gets ten times the load.  
✅ **Backoff with jitter** — Spread retries and give the service room to recover.

**5.** ❌ **Health check that only pings** — The host is up while its database connection is dead.  
✅ **Check the real dependency** — A shallow check sends traffic to a broken app.

## Explained

### The five

1. **No timeouts.** A request with no timeout waits for ever. One hung peer holds a worker, then the next, until the pool is empty. Set connect and read timeouts below your caller's timeout.
   \2. No keep-alive. A new connection per call pays TCP and TLS handshakes before every request, plus slow start. A pool with keep-alive pays once, saving one or two round trips.
   \3. Tiny MTU. An MTU smaller than the path is not a safety net, it is overhead: more packets, more headers, and fragmented UDP. Path MTU discovery depends on ICMP, and a black hole still swallows the message that reports the limit. Match the smallest link, usually 1500 on the internet.
   \4. Retry storms. Retrying immediately, ten times, multiplies load on a service already struggling. Add backoff and jitter, cap the attempts and the total time, and retry only idempotent calls.
   \5. Health checks that lie. A health check that only pings says the machine is up, not that the app can serve. The process may be running with a dead database connection. Check the dependency the request needs, and keep the check cheap enough to run often.

### What they share

Each is cheap to leave alone and expensive to discover.

> **The honest caveat:** a timeout is a guess about the tail. Measure your p99 before you pick five seconds, or you will cut slow but successful requests.

> **The lesson:** the network punishes defaults you never chose.

## In one line

> **The network punishes defaults.** Every one of these is a default somewhere.

**Set one timeout**

```bash
curl --max-time 5 -sI URL
```
