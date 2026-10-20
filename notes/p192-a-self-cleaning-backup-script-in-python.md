---
id: p192
title: "A self-cleaning backup script in Python"
slug: a-self-cleaning-backup-script-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, DevOps, Backup, Linux, Automation]
source: "LinkedIn post P192 · Cloud / DevSecOps series"
linkedin_date: 2027-12-19
design: code
script: backup_rotate.py
---

# A self-cleaning backup script in Python

A backup that fills the disk is a backup that eventually fails. This script makes a compressed, timestamped archive of a folder and then deletes the oldest ones so only the newest N remain. Full file attached, standard library only.

## Quick reference

The full script is at the end of this note: **backup_rotate.py** (standard library only, no `pip install`).

**Run it**

```bash
python3 backup_rotate.py /var/www /backups --keep 7
```

**Example output**

```text
[OK] created www-20261019-020001.tar.gz (84.2 MB)
[OK] keeping 7 most recent backups
```

## Explained

### What it does

It creates prefix-YYYYMMDD-HHMMSS.tar.gz in your backup folder, then lists all backups with that prefix, sorted oldest to newest, and removes everything except the most recent N. The naming means they sort chronologically by default, which is why the cleanup is one line.

### Why it is useful

Most people set up a backup and forget the cleanup, so the disk fills months later at the worst time. This handles both halves: make the backup, and prune the old ones, every run.

### How to use it

`0 2 * * * python3 backup_rotate.py /var/www /backups --keep 7` gives you a week of nightly backups that never grow without bound. Change the path and `--keep` for different folders and retention.

The attached version takes the keep count and a custom prefix, creates the destination if needed, prints the size, and lists what it removed, so your log shows exactly what happened each night.

One honest note: this is a local backup. Follow the 3-2-1 rule and also copy these archives off the server, to object storage or another machine, so a dead disk does not take the backups with it. And test a restore, because a backup you have never opened is only a hope.

## In one line

> **Backups that clean up after themselves.** No full disk, no manual pruning, no forgotten old files.

**Run it nightly**

```bash
0 2 * * * python3 backup_rotate.py /var/www /backups --keep 7
```

## Script: backup_rotate.py

Download: [scripts/backup_rotate.py](../scripts/backup_rotate.py)

```python
#!/usr/bin/env python3
"""backup_rotate.py - timestamped backups that clean up after themselves.

Creates a compressed tar.gz of a source folder into a backup folder, named
with the date and time, then deletes the oldest backups so only the newest N
remain. Standard library only, so it runs anywhere Python does.

Usage:
    python3 backup_rotate.py /var/www /backups
    python3 backup_rotate.py /etc /backups --keep 14 --prefix etc

Cron (daily at 02:00):
    0 2 * * * /usr/bin/python3 /opt/scripts/backup_rotate.py /var/www /backups --keep 7

By s0sta.com
"""
import argparse
import datetime as dt
import sys
import tarfile
from pathlib import Path


def make_backup(src, dest_dir, prefix):
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = dest_dir / f"{prefix}-{stamp}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        tar.add(src, arcname=Path(src).name)
    return out


def rotate(dest_dir, prefix, keep):
    backups = sorted(dest_dir.glob(f"{prefix}-*.tar.gz"))
    removed = []
    while len(backups) > keep:
        old = backups.pop(0)
        old.unlink()
        removed.append(old.name)
    return removed


def main():
    ap = argparse.ArgumentParser(description="Create and rotate tar.gz backups.")
    ap.add_argument("source", help="folder to back up")
    ap.add_argument("dest", help="folder to store backups in")
    ap.add_argument("--keep", type=int, default=7, help="how many backups to keep")
    ap.add_argument("--prefix", help="name prefix, default = source folder name")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        sys.exit(f"source not found: {src}")
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or src.name

    out = make_backup(str(src), dest, prefix)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"[OK] created {out.name} ({size_mb:.1f} MB)")

    removed = rotate(dest, prefix, args.keep)
    for name in removed:
        print(f"[--] removed old backup {name}")
    print(f"[OK] keeping {args.keep} most recent backups")


if __name__ == "__main__":
    main()
```
