---
id: p344
title: "The EXPLAIN cheat sheet"
slug: the-explain-cheat-sheet
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, SQL, QueryTuning, DatabasePerformance, Backend]
source: "LinkedIn post P344 · Data series"
linkedin_date: 2028-12-07
design: cheatsheet
---

# The EXPLAIN cheat sheet

The query is slow, and the first useful thing you can do is ask the planner what it intends to do. EXPLAIN answers that without running the statement.

## Quick reference

### Plan

```sql
EXPLAIN SELECT * FROM orders;
EXPLAIN (FORMAT JSON) SELECT 1;
EXPLAIN (VERBOSE) SELECT * FROM t;
EXPLAIN (COSTS OFF) SELECT * FROM t;
EXPLAIN SELECT * FROM t WHERE id = 1;
```

### Analyse

```sql
EXPLAIN ANALYZE SELECT * FROM orders;
EXPLAIN (ANALYZE, TIMING OFF) SELECT 1;
EXPLAIN (ANALYZE, BUFFERS) SELECT 1;
EXPLAIN (ANALYZE, WAL) SELECT 1;
EXPLAIN (ANALYZE) SELECT count(*) FROM t;
```

### Buffers

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT 1;
SET track_io_timing = on;
SELECT * FROM pg_statio_user_tables;
SELECT * FROM pg_statio_user_indexes;
SHOW track_io_timing;
```

### Read

```sql
EXPLAIN (FORMAT JSON) SELECT * FROM t;
EXPLAIN (ANALYZE, FORMAT JSON) SELECT 1;
EXPLAIN (VERBOSE, FORMAT JSON) SELECT 1;
\x auto
\timing on
```

## Explained

**Plan**  
EXPLAIN prints the plan tree with an estimated cost and row count per node. FORMAT JSON returns the tree as data you can parse, VERBOSE adds output columns, and COSTS OFF strips the estimates when you want only the shape. A Seq Scan on a large table is the line to look for.

**Analyse**  
EXPLAIN ANALYZE runs the statement and adds the actual time and rows per node. It really executes, so a DELETE deletes; wrap it in BEGIN and ROLLBACK. TIMING OFF removes the per-node timing overhead and can make a loop cheaper to measure.

**Buffers**  
EXPLAIN (ANALYZE, BUFFERS) adds shared hit, read, dirtied and written block counts. A hit is a page found in shared buffers; a read is a page fetched from the operating system. pg_statio_user_tables shows the same story per table.

**Read**  
Read the tree from the inside out. The four fields worth naming first are Node Type, Relation Name, Filter and Total Cost. In psql, `\x auto` and \\timing on make the JSON readable, and a Filter on a large scan is a missing index.

> **The honest caveat:** the estimates come from statistics, so a stale ANALYZE makes the planner look wrong for a reason you can fix. Run ANALYZE before you blame the plan.

> **The lesson:** the plan is the query's own account of the work.

## In one line

> **Read the plan before the index.** A plan you cannot read is a query you cannot fix.

**Plan without running**

```sql
EXPLAIN (COSTS OFF) SELECT * FROM t;
```
