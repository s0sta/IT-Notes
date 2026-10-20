---
id: p333
title: "Backups: physical, logical, PITR and the restore test"
slug: backups-physical-logical-pitr-and-the-restore-test
sections: [it]
topic: "Databases & SQL"
tags: [Backups, PostgreSQL, PITR, SRE, DataEngineering]
source: "LinkedIn post P333 · Data series"
linkedin_date: 2028-11-12
design: explainer
---

# Backups: physical, logical, PITR and the restore test

A backup you have never restored is a rumour with a timestamp. Four panels separate what you copy from the test that proves it.

## Quick reference

### Physical backup

- Copies data files block by block
- pg_basebackup or a filesystem snapshot
- Whole cluster, same major version
- Fast restore; no table cherry-picking

### Logical backup

- pg_dump writes SQL or a custom archive
- One database, one schema or one table
- Portable to a newer major version
- Slow restore: every index is rebuilt

### Point in time

- A base backup plus every WAL segment since
- Replay stops at a time, LSN or restore point
- Needs archive_mode and a working archive
- Undoes a bad migration, not one table

### Restore test

- Restore into an isolated instance
- Measure the time, not just the success
- Check row counts and application queries
- Schedule it; a drill you skip is a guess

> **Note:** A physical backup restores the cluster; a logical one restores an object.

## Explained

**Physical backup**  
Three disks stand for the data files copied block by block: pg_basebackup, a filesystem snapshot or a storage clone. It captures the whole cluster at one consistent point, keeps the same major version, and restores quickly because nothing is rebuilt from SQL.

**Logical backup**  
A stack of statements stands for the object copy. pg_dump writes SQL or a custom archive for one database, schema or table; pg_dumpall adds roles and tablespaces. The output loads into a newer major version and restores one table, at the cost of rebuilding every index and replaying every row.

**Point in time**  
The shield in the third panel is the archive. PITR needs a base backup and every WAL segment written since it started. Restore the base, point recovery at the archive, and replay stops at a time, an LSN or a restore point. Lose one segment and the replay stops early.

**Restore test**  
The last panel is a check mark. Restore into an isolated instance, measure the time, run the application's real queries, and compare row counts. A drill you skip is a guess.

> **The honest caveat:** PITR restores the whole cluster to a moment, not one table, and it only works if every WAL segment reached the archive.

> **The lesson:** copy the cluster, copy the objects, replay the WAL, then prove all three with a restore.

## In one line

> **A backup is a tested restore.** A copy is not a backup until a restore has opened it.

**Book the drill**

```bash
pg_basebackup -D /restore -Fp -X stream
```
