---
id: p482
title: "How DNS resolves a name"
slug: how-dns-resolves-a-name
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, Networking, DevOps, SRE, Infrastructure]
source: "LinkedIn post P482 · Network series"
linkedin_date: 2029-10-25
design: architecture
---

# How DNS resolves a name

A deploy is green, the health check passes, and the browser still says the site cannot be found. The application is fine; the name is not.

## Quick reference

- **Stub · Application:** Application (APP) · Resolver library (STUB)
- **Recursive:** Resolver cache (CACHE) · Recursive resolver (REC)
- **Authoritative:** Root servers (ROOT) · TLD servers (TLD) · Zone server (ZONE)

**Request flow:** Application → Resolver library → Recursive resolver → Resolver cache; Recursive resolver → Root servers → TLD servers → Zone server

**Around it:** Browser cache (WEB) · OS stub cache (OS)

## Explained

### Three tiers

The stub resolver is the application's side: getaddrinfo, the resolver library, and the nameservers in `/etc/resolv.conf`. It sends a recursive query and waits.

The recursive resolver does the walking. It checks its cache, then asks a root server, which refers it to the .com TLD servers, which refer it to your zone.

The zone's authoritative server returns the real record with the AA flag. The root and the TLD answer with referrals, not the final address; each is authoritative only for its own piece.

There are thirteen root server identities, anycast across hundreds of sites, and you rarely reach one because a cache answered first.

### The caches

The answer comes back with a TTL, and every cache on the path may keep it for that long. The second lookup stops at the recursive resolver and never reaches the root.

Browser cache and OS stub cache sit outside the tiers and answer before a packet leaves the machine.

> **The honest caveat:** getaddrinfo can answer from `/etc/hosts`, mDNS or a local cache without asking any of these servers, so the diagram is not proof of what your process did.

> **The lesson:** a DNS failure belongs to one tier, and the tier tells you who to call.

## In one line

> **Every lookup is a short walk down.** The answer is cached on the way back, so the second lookup stops early.

**Trace the path**

```bash
dig +trace example.com
```
