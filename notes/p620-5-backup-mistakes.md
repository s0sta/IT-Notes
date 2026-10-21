---
id: p620
title: "5 backup mistakes"
slug: 5-backup-mistakes
sections: [it, devsecops]
topic: "Backup & recovery"
tags: [Backup, DisasterRecovery, SRE, DevOps, Security]
source: "LinkedIn post P620 · PythonFixes series"
linkedin_date: 2030-09-12
design: dontdo
---

# 5 backup mistakes

The region goes down at 04:00 and the backup bucket is in it. Five mistakes turn a backup plan into a story about one.

## Quick reference

**1.** ❌ **Never restore-test** — A backup that never restored is a hope, not a copy.  
✅ **Drill one restore a month** — One path, off the backup host, timed and logged.

**2.** ❌ **Keep one copy, one region** — The region that holds the bucket can be the region that fails.  
✅ **Copy to a second region** — Cross-region replication with its own credentials.

**3.** ❌ **No retention policy** — Every backup is kept, so the bill grows and the restore slows.  
✅ **Retention: 7d, 4w, 12m** — Seven daily, four weekly, twelve monthly, then delete.

**4.** ❌ **Unencrypted backups** — A stolen archive is the production database in a bag.  
✅ **Encrypt at write, key separate** — The key lives in KMS, not on the backup host.

**5.** ❌ **No owner on the backup** — Nobody knows what is inside, so nobody deletes it.  
✅ **Owner and purpose tag** — A name and a restore purpose, checked each quarter.

## Explained

### The five

1. **Never restore-test.** A backup that never restored is a hope, not a copy. Drill one restore a month: one path, off the backup host, timed and logged.
   \2. Keep one copy, one region. The region that holds the bucket can be the region that fails. Copy to a second region with its own credentials.
   \3. No retention policy. Every backup is kept, so the bill grows and the restore slows. Seven daily, four weekly and twelve monthly is a start; delete the rest on a schedule.
   \4. Unencrypted backups. A stolen archive is the production database in a bag. Encrypt at write and keep the key in KMS, not on the backup host.
   \5. No owner on the backup. Nobody knows what is inside, so nobody deletes it. Put an owner and a restore purpose in the tag, and check it each quarter.

### What they share

Each one is invisible while the job is green. The first restore is where they all arrive at once.

> **The honest caveat:** a backup is a process, not a file. The policy, the key and the owner are the parts people skip, and they are the parts an audit asks for.

> **The lesson:** a backup is a promise, and a restore is the only proof.

## In one line

> **One copy is not a backup.** Five mistakes, each one a restore that will not happen.

**Restore one file**

```bash
tar -xzf backup.tgz -C /tmp/r
```
