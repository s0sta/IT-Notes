---
id: p346
title: "Partitioning a big table, drawn"
slug: partitioning-a-big-table-drawn
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, DatabaseDesign, Partitioning, DataEngineering, Backend]
source: "LinkedIn post P346 · Data series"
linkedin_date: 2028-12-12
design: architecture
---

# Partitioning a big table, drawn

The orders table passed four hundred million rows, and the delete at the end of the month now takes longer than the month. Partitioning changes what the delete has to touch.

## Quick reference

- **Tier 1 · Planner:** Query (SQL) · Partition key (KEY)
- **Tier 2 · Partitions:** Range (RANGE) · Hash (HASH) · List (LIST)
- **Tier 3 · Archive:** Cold store (COLD) · Retention (TTL)

**Request flow:** Query → Partition key → Range → Cold store → Retention; Partition key → Hash; Partition key → List

## Explained

**Planner**  
A partitioned table is one logical table with many physical children. The query names the partition key, and the planner prunes: it opens only the partitions whose bounds can match the WHERE clause. A query without the key opens every partition, which is the failure this design invites.

**Partitions**  
Range partitioning by month suits time-series data, because each child has known bounds and a new month is a new child. Hash spreads rows evenly when there is no natural range and you only need a smaller unit of maintenance. List gives one partition per known value, such as region or status. Range answers when, list answers what value, and hash answers neither.

**Archive**  
Old partitions are detached, not deleted row by row. The cold store holds them compressed, and the retention rule drops or archives the oldest. A detach is a metadata change; a DELETE is a long transaction that leaves bloat behind.

> **The honest caveat:** partitioning helps when queries filter on the key. Every unique index must include the partition key, planning time grows with the number of partitions, and a default partition quietly collects everything you forgot to route.

> **The lesson:** partitioning is a routing decision, and the key is the route.

## In one line

> **Cut the table, keep the query.** The win is the partitions the planner never opens.

**See the partitions**

```sql
SELECT * FROM pg_partition_tree('orders');
```
