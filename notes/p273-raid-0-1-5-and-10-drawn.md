---
id: p273
title: "RAID 0, 1, 5 and 10, drawn"
slug: raid-0-1-5-and-10-drawn
sections: [it]
topic: "Storage & infrastructure"
tags: [Linux, Storage, RAID, SysAdmin, DataProtection]
source: "LinkedIn post P273 · Visual series"
linkedin_date: 2028-06-25
design: explainer
---

# RAID 0, 1, 5 and 10, drawn

RAID combines disks so that one failure is survivable, or so that several disks behave like one fast one. The level you choose is a trade between speed, capacity and how many drives you can lose.

## Quick reference

### RAID 0 - Striping

- Data split across 2+ drives
- Full capacity, best speed
- No redundancy: one loss, all lost
- Good for scratch, caches

### RAID 1 - Mirroring

- Every write copied to both
- Survives one drive failure
- Half the capacity
- Good for boot and small data

### RAID 5 - Striping + parity

- Minimum 3 drives, parity spread
- Tolerates 1 drive failure
- Capacity of n-1 drives
- Good for file servers

### RAID 10 - Mirrored stripe

- Minimum 4 drives, pairs then stripes
- Tolerates one loss per pair
- Half the capacity, fast rebuild
- Good for databases

> **Note:** RAID is not a backup: keep an external or cloud copy, and test the restore.

## Explained

RAID 0 stripes data across drives. You get the full capacity and the best speed, and you get no protection at all: lose one drive and the set is gone. It belongs on scratch space, never on data you cannot rebuild.

RAID 1 mirrors every write to two drives. One drive can fail and the server keeps running, at the cost of half your capacity. It is the standard choice for boot disks and small datasets.

RAID 5 stripes data with parity spread across the set. It needs at least three drives, survives one failure, and gives you the capacity of all but one drive. Rebuilds are slow and put the remaining drives under load, which is why large drives make RAID 5 uncomfortable.

RAID 10 mirrors pairs and stripes across them. It needs at least four drives, survives one failure per pair, and rebuilds fast. For databases, the speed and rebuild time are usually worth the 50 percent capacity cost.

> **The rule that outranks all four:** RAID is not a backup. It protects against a dead disk, not against a deleted table, ransomware or a bad deploy.

## In one line

> **Redundancy is not backup.** A mirrored disk survives a disk, not a delete.

**Check the array**

```bash
cat /proc/mdstat
```
