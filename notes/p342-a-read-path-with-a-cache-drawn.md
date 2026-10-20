---
id: p342
title: "A read path with a cache, drawn"
slug: a-read-path-with-a-cache-drawn
sections: [it]
topic: "Databases & SQL"
tags: [Databases, Redis, Caching, Backend, SystemDesign]
source: "LinkedIn post P342 · Data series"
linkedin_date: 2028-12-03
design: architecture
---

# A read path with a cache, drawn

The dashboard is slow at nine in the morning, and the database is not the first place to look. The read path has three tiers, and each one is allowed to answer without the next.

## Quick reference

- **Tier 1 · App:** Application (APP) · Connection pool (POOL)
- **Tier 2 · Cache:** Local cache (L1) · Redis (L2)
- **Tier 3 · Data:** Read replica (RO) · Primary (RW)

**Request flow:** Application → Connection pool → Primary; Application → Local cache → Redis → Read replica

## Explained

**Application**  
The request arrives at the application, which asks its connection pool for a session. The pool decides whether to reuse an open connection or pay for a new one, and that wait happens before any SQL runs. On a busy box the pool is the queue, not the database.

**Cache**  
The application checks its local cache first: an in-process map with no network hop and no shared state. A miss goes to Redis, one round trip away and shared by every instance. A hit there returns in a fraction of a millisecond; a miss costs the second hop and sends the query onward.

**Data**  
Only the third miss reaches PostgreSQL. Reads go to the read replica, writes go through the pool to the primary, and replication is asynchronous, so a read immediately after a write can return the old row. That is the gap the cache hides, not the gap it closes.

> **The honest caveat:** a cache is a second copy of the truth. Every entry needs a time to live, an invalidation rule on write, and a decision about what stale means for the page.

> **The lesson:** each tier removes a round trip, and each round trip you remove is a failure mode you no longer have to debug.

## In one line

> **Cache the read, not the write.** The read path is where the latency lives, and where the stale data hides.

**See the hit rate**

```bash
redis-cli info stats | grep keyspace
```
