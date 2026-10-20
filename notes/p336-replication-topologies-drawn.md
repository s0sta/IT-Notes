---
id: p336
title: "Replication topologies, drawn"
slug: replication-topologies-drawn
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, Replication, Databases, SRE, DataEngineering]
source: "LinkedIn post P336 · Data series"
linkedin_date: 2028-11-19
design: architecture
---

# Replication topologies, drawn

The primary is easy. The hard part of replication is deciding which replica answers a read, and what the application is allowed to assume when it does.

## Quick reference

- **Tier 1 · Writer:** Primary (PRIM) · WAL sender (WALS)
- **Tier 2 · Replicas:** Sync replica (SYNC) · Async replica (ASYNC) · Cascading replica (CASC)
- **Tier 3 · Read path:** Application (APP) · Read router (RTR)

**Request flow:** Primary → Sync replica → Read router; Primary → Async replica → Cascading replica; Async replica → Read router; Application → Read router

## Explained

**Writer**  
The writer tier is the primary and its WAL sender. The primary accepts every write and writes WAL; a WAL sender process per replica streams those records. There is still exactly one writer, which is why replication scales reads and not writes.

**Replicas**  
The sync replica acknowledges the WAL before the primary reports a commit, so a committed transaction survives its failure, at the cost of a network round trip on every write. The async replica acknowledges nothing, so it lags and a failover can lose the last few transactions. The cascading replica streams from the async replica rather than the primary, which removes load from the writer and adds the upstream delay to its own.

**Read path**  
Underneath, the application talks only to the read router, and the router chooses a replica for each read-only query. The router needs a policy for lag: send reads to the sync replica when freshness matters, spread them across the others when throughput matters, and send read-after-write traffic to the primary.

> **The honest caveat:** synchronous replication waits for the standby to flush WAL, not to apply it, so a sync replica can still return a slightly stale snapshot unless you use remote_apply.

> **The lesson:** replication gives you copies, not consistency; the router is where you decide which copy is good enough.

## In one line

> **One writer, many copies.** Copies are cheap; knowing which copy to read is not.

**Read the lag**

```sql
SELECT * FROM pg_stat_replication;
```
