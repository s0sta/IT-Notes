---
id: p339
title: "5 database mistakes and the fix for each"
slug: 5-database-mistakes-and-the-fix-for-each
sections: [it]
topic: "Databases & SQL"
tags: [Databases, PostgreSQL, SRE, Backups, DataEngineering]
source: "LinkedIn post P339 · Data series"
linkedin_date: 2028-11-26
design: dontdo
---

# 5 database mistakes and the fix for each

Every database incident review ends with a short list that was visible for months. Each is cheap to fix before the incident and expensive to explain after it.

## Quick reference

**1.** ❌ **Backups never restored** — A backup that fails to restore is a file, not a backup.  
✅ **A restore drill each month** — The drill measures RTO and proves the files open.

**2.** ❌ **Indexes added and never reviewed** — Every index slows writes and costs disk.  
✅ **Review slow queries monthly** — Add what the plan needs; drop what nothing uses.

**3.** ❌ **Transactions held open for hours** — Old snapshots stop vacuum cleaning dead rows.  
✅ **Keep transactions short** — Short transactions free space and locks sooner.

**4.** ❌ **The app connects as superuser** — One injection can drop every database.  
✅ **Least-privilege app role** — The app cannot drop what it cannot reach.

**5.** ❌ **SELECT \* in every query** — It moves columns the code never reads.  
✅ **Name the columns you use** — Covering indexes can answer from the index.

## Explained

### The five

1. **Backups never restored.** The job writes a file nightly, the dashboard stays green, and the restore fails at 2 a.m. because the WAL archive stopped three weeks ago. Run a restore drill each month, measure the time, and run a real query.

2. **Indexes added and never reviewed.** Every index speeds one read, slows every write and takes disk. Review the slow query log, add what the workload needs, drop what nothing uses.

3. **Transactions held open for hours.** A long transaction keeps an old snapshot alive, and in PostgreSQL that stops vacuum removing dead rows. It also holds locks. Commit before the next network call.

4. **The app connects as superuser.** One injection or one bad migration then has the rights to drop every database. Give the app a least-privilege role and a separate migration role.

5. **SELECT \* in every query.** It moves columns the code never reads, defeats covering indexes and breaks when a column is renamed or reordered. Name the columns you use.

### What they share

Each is a convenience that became a default, invisible to a single code review.

> **The honest caveat:** SELECT \* in an ad hoc psql query is fine; the rule is about code paths that run a million times a day.

> **The lesson:** the database keeps the receipt for every shortcut, and it presents the bill during an incident.

## In one line

> **Small habits, large outages.** The bill arrives in the incident review, not the invoice.

**Count the roles**

```sql
SELECT rolname FROM pg_roles;
```
