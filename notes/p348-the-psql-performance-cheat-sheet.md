---
id: p348
title: "The psql performance cheat sheet"
slug: the-psql-performance-cheat-sheet
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, SQL, DatabasePerformance, psql, SRE]
source: "LinkedIn post P348 · Data series"
linkedin_date: 2028-12-17
design: cheatsheet
---

# The psql performance cheat sheet

A report is slow and nobody changed the code. Before you read a plan, read what the server is doing right now, because the plan will not tell you who is blocking the table.

## Quick reference

### Activity

```sql
SELECT * FROM pg_stat_activity;
SELECT pid, state FROM pg_stat_activity;
SELECT count(*) FROM pg_stat_activity;
\watch 2
```

### Locks

```sql
SELECT * FROM pg_locks WHERE NOT granted;
SELECT locktype, mode FROM pg_locks;
SELECT * FROM pg_blocking_pids(1234);
SELECT locktype, relation FROM pg_locks;
```

### Statements

```sql
CREATE EXTENSION pg_stat_statements;
SET pg_stat_statements.track = 'all';
SELECT * FROM pg_stat_statements LIMIT 5;
SELECT * FROM pg_stat_user_functions;
```

### Sizes

```sql
SELECT pg_database_size('db');
SELECT pg_total_relation_size('t');
SELECT pg_relation_size('t');
SELECT pg_size_pretty(123456789);
\dt+
```

## Explained

**Activity**  
pg_stat_activity has one row per connection: state, query, wait event and how long the current query has run. A session idle in transaction is the one holding locks while doing nothing. `\watch 2` re-runs the query every two seconds, which is enough to watch a queue build.

**Locks**  
pg_locks shows every lock, granted or not. A row with granted false is a queue, and pg_blocking_pids names the sessions in front of it. Cancel the blocker with pg_cancel_backend before you terminate it, because a terminate rolls the transaction back and can take longer.

**Statements**  
pg_stat_statements aggregates by query shape: calls, total time, mean time and rows. Create the extension, set track to all to include statements inside functions, and read the top five by total time rather than by mean.

**Sizes**  
pg_database_size, pg_relation_size and pg_total_relation_size return bytes; pg_size_pretty makes them readable. `\dt+` lists tables with their size, which is the fastest way to find the one behind the slow count.

> **The honest caveat:** these views are cumulative since the last reset, and pg_stat_statements needs shared_preload_libraries plus a restart, so a managed service may not offer it at all.

> **The lesson:** the server will tell you where the time goes if you ask the right view.

## In one line

> **Ask the server, not the hunch.** The views know what the plan only estimates.

**Find the long query**

```sql
SELECT * FROM pg_stat_activity;
```
