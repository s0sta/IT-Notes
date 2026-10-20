---
id: p341
title: "Quiz: 3 database operations questions"
slug: quiz-3-database-operations-questions
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, Replication, Backups, Databases, DataEngineering]
source: "LinkedIn post P341 · Data series"
linkedin_date: 2028-11-30
design: quiz
---

# Quiz: 3 database operations questions

Three questions separate a team that has run a database from one that has only read about it. Each answer is one mechanism, and each mechanism has a cost.

## Quick reference

**Q1. A read replica lags by two seconds. Why can a user see stale data?**

- a) It applies the primary's WAL after the commit
- b) The replica caches every query for two seconds
- c) The primary sends reads to the replica first

> **Answer:** a) It applies the primary's WAL after the commit. Replication is asynchronous by default: the primary commits, then ships WAL, and the replica applies it later. A read in that window sees the older snapshot.

**Q2. What does point-in-time recovery need to restore to 09:15?**

- a) A base backup plus every WAL segment since it
- b) A nightly logical dump and the current schema
- c) A replica promoted at 09:15

> **Answer:** a) A base backup plus every WAL segment since it. PITR restores the base backup, then replays archived WAL to the target time. Without the WAL archive you can only return to the backup's moment.

**Q3. Why does PostgreSQL need VACUUM after heavy updates?**

- a) Dead row versions still occupy pages
- b) It compresses every table and index
- c) It rewrites the WAL so recovery is faster

> **Answer:** a) Dead row versions still occupy pages. An UPDATE writes a new row version and leaves the old one dead. VACUUM marks that space reusable and updates the visibility map; it does not rewrite the table.

## Explained

**The stale replica**  
Why can a replica serve stale reads? Because replication is asynchronous by default: the primary commits and returns, then ships WAL, and the replica applies it later. A read that arrives in that window sees the older snapshot. The fix is not to trust every replica for every read: route read-after-write traffic to the primary, or track the replay position.

**The recovery chain**  
What does point-in-time recovery need? A base backup and every WAL segment written since it. Restore the base, point recovery at the archive, and replay stops at the target time. Without the archive you can only return to the moment of the backup, which is rarely the moment you need.

**The vacuum debt**  
Why does PostgreSQL need VACUUM after heavy updates? An UPDATE writes a new row version and leaves the old one dead. VACUUM marks that space reusable and updates the visibility map; it does not rewrite the table. Without it, dead rows pile up, scans read more pages and the table grows even though the live row count is flat.

> **The honest caveat:** PITR is only as good as the archive, so check pg_stat_archiver for failed segments before you need a restore.

> **The lesson:** know what each operation promises, and know the gap it leaves.

## In one line

> **Know the copy, know the gap.** Every operation has a promise and a gap.

**Check the archive**

```sql
SELECT * FROM pg_stat_archiver;
```
