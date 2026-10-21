---
id: p484
title: "DNS TTL and failover"
slug: dns-ttl-and-failover
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, Networking, SRE, DevOps, Infrastructure]
source: "LinkedIn post P484 · Network series"
linkedin_date: 2029-10-30
design: explainer
---

# DNS TTL and failover

You lower the TTL, change the record, and the old address keeps serving traffic for another hour. The change worked; the caches did not hear about it.

## Quick reference

### TTL

- The authoritative server sets it, per record
- A resolver may cache for up to that long
- 300 is five minutes; 86400 is one day

### Caches

- Browser, OS, stub and recursive resolver
- Each keeps its own copy and its own timer
- A cache hit never reaches your zone

### Failover

- Health checks swap the answer to a standby
- Clients keep the old address until TTL ends
- Live TCP connections are not moved by DNS

### Propagation

- No push exists; answers wait to expire
- Wait one old TTL before you judge a change
- Lower the TTL a day early, raise it after

> **Note:** A record change is live only when the last cache that matters expires.

## Explained

### The timer

TTL is a number of seconds on each record, set by the zone. It is the maximum time a resolver may cache the answer, so 300 means five minutes and 86400 means a day.

### The caches

A lookup can stop at the browser, the OS stub or the recursive resolver. Each keeps its own copy and its own countdown, and only a miss reaches your authoritative zone.

The authoritative server is the source, not a cache: it answers from the zone every time it is asked.

### The failover

A health check can swap the answer to a standby address. Clients that already hold the old address keep using it until its TTL expires, and a live TCP connection stays on the old address whatever DNS says next.

### The wait

Propagation is not a push. It is the time for caches to expire, so lower the TTL at least one old TTL before the change and raise it again after the cutover.

> **The honest caveat:** lowering the TTL does not flush a cache that already holds the old record, and some resolvers enforce a minimum TTL while JVMs and browsers keep their own caches.

> **The lesson:** a failover plan that ignores TTL is a hope with a diagram.

## In one line

> **The old answer has a timer.** Propagation is not a delay you can skip; it is a cache expiring.

**Watch the ttl**

```bash
dig example.com +noall +answer
```
