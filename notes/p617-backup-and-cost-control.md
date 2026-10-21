---
id: p617
title: "Backup and cost control"
slug: backup-and-cost-control
sections: [it, devsecops]
topic: "Backup & recovery"
tags: [Backup, DevOps, SRE, CloudCost, DisasterRecovery]
source: "LinkedIn post P617 · PythonFixes series"
linkedin_date: 2030-09-05
design: architecture
---

# Backup and cost control

The backup run is green and the bill is real. Three tiers decide whether the copy is cheap and whether it is true.

## Quick reference

- **Backup:** Volume snapshot (SNAP) · Object archive (ARCH)
- **Verify:** Restore drill (DRILL) · Checksum (HASH)
- **Retire:** Retention policy (KEEP) · Delete (DEL)

**Request flow:** Volume snapshot → Restore drill → Retention policy → Delete; Object archive → Checksum → Retention policy

**Around it:** Exit code (EXIT) · Cost report (COST)

## Explained

### Backup

A volume snapshot for the fast copy, and an object archive for the slow one. The snapshot is the one you restore today; the archive is the one you keep for the year. Both are useless until something proves them.

### Verify

A restore drill for the path, and a checksum for the bytes. The drill opens the archive, lists the expected paths and fails on a missing one; the checksum catches a file that changed after it was written. The drawing runs from each backup node to its check, then both checks feed retention.

### Retire

A retention policy and a delete step. The policy says what stays: seven daily, four weekly, twelve monthly. The delete step runs on a schedule, so the archive does not become the largest line on the invoice.

### The flow

Snapshot to drill, archive to checksum, drill and checksum to retention, retention to delete. Two nodes per tier, five arrows, one exit code.

> **The honest caveat:** verification costs time and compute, and a checksum is not a restore. The drill is the only tier that proves the data is readable.

> **The lesson:** a backup is a process with three tiers, not a file in a bucket.

## In one line

> **Take the copy, then test the copy.** The copy that restores is the only one worth paying for.

**Drill the archive**

```bash
python3 restore_drill.py backup.tar
```
