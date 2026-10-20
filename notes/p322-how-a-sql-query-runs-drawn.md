---
id: p322
title: "How a SQL query runs, drawn"
slug: how-a-sql-query-runs-drawn
sections: [it]
topic: "Databases & SQL"
tags: [SQL, PostgreSQL, Databases, DataEngineering, Performance]
source: "LinkedIn post P322 · Data series"
linkedin_date: 2028-10-17
design: architecture
---

# How a SQL query runs, drawn

You press enter on a SELECT and the rows come back in milliseconds. Between the two, the query crosses three tiers, and each one can be the reason it is slow.

## Quick reference

- **Client:** driver (DRV) · connection pool (POOL)
- **Engine:** parser (PARSE) · planner (PLAN) · executor (EXEC)
- **Storage:** buffer cache (CACHE) · heap files (HEAP) · indexes (IDX) · WAL (WAL)

**Request flow:** driver → connection pool → parser → planner → executor → buffer cache → heap files; buffer cache → indexes; executor → WAL

## Explained

**Client**  
The driver speaks the database protocol, binds your parameters and returns typed rows. A connection pool keeps a handful of physical connections open, so the next query does not pay for TCP, TLS and authentication again.

**Engine**  
The parser turns the text into a syntax tree and checks it against the system tables; a typo fails here. The planner estimates how many rows each step will touch, using the statistics the last ANALYZE collected, then chooses a seq scan or an index, a nested loop or a hash join. The executor pulls rows through that plan, one node at a time, and asks the buffer cache for pages.

**Storage**  
The buffer cache holds hot 8 kB pages in shared memory. A miss reads from the heap files that hold the table, or from an index, and a write first appends to the WAL so a crash can replay it. The heap is where the rows live; the index is only a map to them.

> **The honest caveat:** this is PostgreSQL's shape. MySQL, SQL Server and SQLite do the same work under different names, and some engines fuse the parser and planner into one step.

> **The lesson:** when a query is slow, ask which tier is doing the work, not which tier looks busy.

## In one line

> **Parse it, plan it, then read pages.** A query is a path through three tiers, and the slowest step owns the latency.

**Read the plan**

```sql
EXPLAIN ANALYZE SELECT * FROM t;
```
