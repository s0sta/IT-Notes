---
id: p579
title: "Four host failure modes"
slug: four-host-failure-modes
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SysAdmin, SRE, DevOps, ITInfrastructure]
source: "LinkedIn post P579 · PythonFixes series"
linkedin_date: 2030-06-09
design: explainer
---

# Four host failure modes

At 03:00 the pager sends the same sentence four times in a month: the host is unhealthy. Four failures look alike from the alert and nothing alike from a shell.

## Quick reference

### Disk full

- `df -h` shows 100%, writes return ENOSPC
- Logs, images and backups, never rotated
- `lsof +L1` finds a deleted file still open
- Fix: rotate, then truncate, not rm

### Inodes full

- `df -h` says 40% free, `df -i` says 100%
- One inode per file, 256 bytes each
- Millions of session or cache files
- Fix: find the directory that grew

### OOM killer

- The kernel kills to keep the box alive
- dmesg keeps the pid, RSS and score
- The highest oom_score dies first
- Fix: cap the unit with MemoryMax

### fd exhaustion

- Every socket, pipe and file takes one slot
- The default soft limit is often 1024
- The process logs EMFILE: too many files
- Fix: close in finally, raise LimitNOFILE

> **Note:** Four ways a healthy host stops working.

## Explained

### Disk full

`df -h` shows 100% and every write returns ENOSPC. The usual cause is a log, an image layer or a backup that nobody rotated. A deleted file still held open keeps its blocks: `lsof +L1` finds space that du cannot see, and restarting the writer returns it.

### Inodes full

`df -h` shows 40% free while `df -i` shows 100%. The filesystem has blocks and no inode to describe a new file, because ext4 allocates one inode per 16 KB and each one costs 256 bytes. Millions of session or cache files do this, and the fix is the directory that grew.

### OOM killer

The kernel kills a process to keep the box alive. dmesg keeps the pid, the resident memory and oom_score_adj, and the highest score dies first. A cgroup memory limit contains the damage to one service, not the whole host.

fd exhaustion

Every socket, pipe and open file takes a descriptor. The default soft limit is often 1024, and a leak reaches it in days. The process logs EMFILE: too many open files, which reads like a network error until you count.

> **The honest caveat:** two of these can be true at once. A log flood fills the disk, the writer blocks, and the OOM killer arrives to finish the job.

> **The lesson:** the symptom names the tier, and the tool names the cause.

## In one line

> **Same page, four causes.** The symptom names the tier; the tool names the cause.

**Check both**

```bash
df -h; df -i
```
