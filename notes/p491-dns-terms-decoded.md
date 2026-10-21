---
id: p491
title: "DNS terms, decoded"
slug: dns-terms-decoded
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, Networking, DevOps, SRE, Infrastructure]
source: "LinkedIn post P491 · Network series"
linkedin_date: 2029-11-15
design: reveal
---

# DNS terms, decoded

A lookup that fails is usually a vocabulary problem before it is a technical one. Six words cover most of the conversation.

## Quick reference

- **A / AAAA** — Address records: A holds one IPv4 address, AAAA holds one IPv6 address, and a name can carry several of each.
- **CNAME** — Canonical name: an alias pointing at another name. The resolver follows the chain and returns the target's address.
- **TTL** — Time to live: the seconds a resolver may cache the answer. The zone sets it; every cache counts it down.
- **Resolver** — The recursive server that walks root, TLD and zone for you, then caches what it finds for the TTL.
- **Authoritative** — The nameserver that holds the zone and gives the real answer, with the AA flag set.
- **Propagation** — Not a push: the wait for caches to expire. No update is pushed to caches; old answers simply time out.

## Explained

### The records

A and AAAA are address records: A holds one IPv4 address, AAAA holds one IPv6 address, and a name can carry several of each. The AAAA record is pronounced quad A, and it does not replace the A record; the two usually sit side by side.

CNAME is a canonical name, an alias pointing at another name. The resolver follows the chain and returns the target's address, while the URL in the browser stays the same.

### The timer

TTL is the time to live in seconds: the longest a resolver may cache the answer. The authoritative server sets it, and every cache counts it down.

### The servers

The resolver is the recursive server that walks root, TLD and zone for you, then caches what it finds.

The authoritative server holds the zone and gives the real answer, with the AA flag set.

### The wait

Propagation is not a push. It is the wait for caches to expire; no update is pushed to them, and old answers simply time out. That is why one change looks live for some users and stale for others.

> **The honest caveat:** TTL is a maximum, not a promise; resolvers can clamp it, and browsers and JVMs keep caches with their own TTLs.

> **The lesson:** learn the words and the diagram draws itself.

## In one line

> **Learn the words, read the answer.** A vocabulary turns a failed lookup into a diagram.

**Decode a lookup**

```bash
dig +trace example.com
```
