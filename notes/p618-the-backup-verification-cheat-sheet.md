---
id: p618
title: "The backup verification cheat sheet"
slug: the-backup-verification-cheat-sheet
sections: [it, devsecops]
topic: "Backup & recovery"
tags: [Backup, Linux, DevOps, SRE, CloudStorage]
source: "LinkedIn post P618 · PythonFixes series"
linkedin_date: 2030-09-08
design: cheatsheet
---

# The backup verification cheat sheet

A backup nobody opened is a hope with a schedule. Four blocks of commands turn the hope into evidence.

## Quick reference

### Archive

```bash
tar -czf /backup/etc.tgz /etc
tar -tzf /backup/etc.tgz | head
aws s3 cp etc.tgz s3://bkp/etc/
sha256sum /backup/etc.tgz
```

### Test

```bash
tar -xzf /backup/etc.tgz -C /tmp/r
tar -df /backup/etc.tgz
sha256sum -c SHA256SUMS
diff -r /etc /tmp/r/etc | head
```

### Retention

```bash
find /backup -mtime +30 -type f
find /backup -type f -ls
logrotate -d /etc/logrotate.d/bkp
aws s3 rm s3://bkp/old/ --dryrun
```

### Cost

```bash
du -sh /backup/*
du -h --max-depth=1 /backup
aws s3 ls s3://bkp --recursive --summarize
aws s3 ls s3://bkp --recursive
```

## Explained

### Archive

`tar -czf /backup/etc.tgz /etc` builds the archive. `tar -tzf /backup/etc.tgz | head` lists it without writing a file. `aws s3 cp etc.tgz s3://bkp/etc/` moves the copy off the host. `sha256sum /backup/etc.tgz` prints the digest, and the digest belongs beside the archive, not in a chat message.

### Test

`tar -xzf /backup/etc.tgz -C /tmp/r` extracts to a scratch directory. `tar -df /backup/etc.tgz` compares the archive with the filesystem. `sha256sum -c SHA256SUMS` verifies the digest. diff -r `/etc /tmp/r/etc |` head shows what differs.

### Retention

`find /backup -mtime +30 -type f` lists what is older than the policy. `find /backup -type f -ls` shows the size and the path. `logrotate -d /etc/logrotate.d/bkp` tests the rule without moving a file. `aws s3 rm s3://bkp/old/ --dryrun` shows what a delete would remove.

### Cost

`du -sh /backup/*` shows the big directories. `du -h --max-depth=1 /backup` shows the split. `aws s3 ls s3://bkp --recursive --summarize` totals the objects. `aws s3 ls s3://bkp --recursive` lists every object and its size.

> **The honest caveat:** a checksum proves the copy matches the digest, not that the archive holds the data you need. Only a restore into a scratch directory proves that.

> **The lesson:** the archive is the easy part; the test is the work.

## In one line

> **A backup you never opened is a hope.** The commands are cheap; the restore is the proof.

**Open one archive**

```bash
tar -tzf /backup/etc.tgz | head
```
