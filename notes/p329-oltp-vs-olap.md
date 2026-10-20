---
id: p329
title: "OLTP vs OLAP"
slug: oltp-vs-olap
sections: [it]
topic: "Databases & SQL"
tags: [Databases, OLTP, OLAP, DataEngineering, SQL]
source: "LinkedIn post P329 · Data series"
linkedin_date: 2028-11-02
design: compare
---

# OLTP vs OLAP

The dashboard query takes forty seconds and the checkout query takes four milliseconds, and both run on the same server. That gap is the OLTP and OLAP split, and it starts in how the data is stored.

## Quick reference

| | **OLTP** | **OLAP** |
|:--|:--|:--|
| Workload | Short writes, point reads | Long scans, aggregates |
| Typical query | One row by primary key | Millions of rows, grouped |
| Indexes | Many, narrow, covering | Few, columnar, compressed |
| Storage | Row store, 8 kB pages | Column store, compressed |
| Latency | Milliseconds per query | Seconds to minutes |
| Scale by | More connections, sharding | More workers, partitions |

**OLTP** (Many short reads and writes): The checkout database: many short transactions, one row at a time.

```bash
pgbench -c 32 -T 60
```

**OLAP** (Few large scans, many columns): The warehouse: few long scans, many columns, one answer.

```sql
SELECT count(*) FROM events;
```

- OLTP → write fast, read one row, stay correct.
- OLAP → read everything, once, and forgive latency.

## Explained

**The workload**  
OLTP is the database behind checkout: many short transactions, each reading or writing one row by primary key. Latency is the product, so it is measured in milliseconds and the schema is normalised to keep writes cheap. OLAP is the warehouse behind the dashboard: few queries, each scanning millions of rows and grouping them. Throughput matters more than per-query latency.

**The storage**  
A row store keeps a whole row together, so a point lookup reads one page. A column store keeps each column apart and compresses it, so a scan of three columns never touches the other thirty. That is why an OLTP index is narrow and many, and an OLAP table is wide, partitioned and columnar.

**Where the line blurs**  
Some managed warehouses now offer row-store tables for small dimensions, and PostgreSQL extensions add columnar storage to an OLTP database. The labels describe a workload, not a product.

> **The honest caveat:** a small warehouse on a row store can beat a badly modelled column store, and an HTAP system that claims both usually pays for it somewhere. Measure your queries before you move them.

> **The lesson:** choose the workload first, then the storage; the label is a shortcut, not a specification.

OLTP writes the row.  
OLAP reads the world.
