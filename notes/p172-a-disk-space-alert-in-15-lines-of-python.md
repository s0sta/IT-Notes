---
id: p172
title: "A disk-space alert in 15 lines of Python"
slug: a-disk-space-alert-in-15-lines-of-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, SysAdmin, DevOps, Automation]
source: "LinkedIn post P172 · Cloud / DevSecOps series"
linkedin_date: 2027-11-02
design: code
script: disk_alert.py
---

# A disk-space alert in 15 lines of Python

Phase 1 of my Cloud/DevSecOps plan is Linux and automation, so here is the first of a few real Python scripts you can use at work today. This one warns you before a disk fills up. The full file is attached and runs on any server with Python, no libraries to install.

## Quick reference

The full script is at the end of this note: `disk_alert.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 disk_alert.py
```

**Example output**

```text
ALERT / at 91%
```

## Explained

### What it does

It checks the usage of each path you list. If any crosses the threshold, it prints an ALERT and exits with code 1, so cron, a monitoring agent or a CI step all understand that something is wrong. Exit 0 means all good.

### Why the standard library only

shutil.disk_usage comes with Python. No pip install, nothing to break on an old server. That matters when you are dropped onto a machine you do not control.

### How to use it

Save it, then schedule it: `*/30 * * * * /usr/bin/python3 /opt/scripts/disk_alert.py >> /var/log/disk_alert.log 2>&1`. Now you get a line in a log the moment a disk gets tight, instead of finding out when the database stops writing.

The real version, attached, adds command-line options for the threshold and paths, shows human-readable sizes, and includes the hostname so one log can cover many servers.

> **The lesson behind it:** a full disk is never sudden. It is unwatched. Fifteen lines and a cron entry turn "unwatched" into "I knew yesterday".

## In one line

> **Automate the boring checks.** A cron job and a few lines beat a 2 a.m. outage.

**Run it every 30 min**

```bash
*/30 * * * * python3 disk_alert.py
```

## Script: disk_alert.py

Download: [scripts/disk_alert.py](../scripts/disk_alert.py)

```python
#!/usr/bin/env python3
"""disk_alert.py - warn before a disk fills up.

Checks the usage of one or more paths and prints an ALERT for any that
cross a threshold. Exit code is 1 if anything alerted, so it works in cron
and in monitoring. Standard library only.

Usage:
    python3 disk_alert.py                 # checks / and /var at 85%
    python3 disk_alert.py -t 90 / /data   # custom threshold and paths

Cron (every 30 min):
    */30 * * * * /usr/bin/python3 /opt/scripts/disk_alert.py >> /var/log/disk_alert.log 2>&1

By s0sta.com
"""
import argparse
import shutil
import socket
import sys


def pct_used(path):
    total, used, _free = shutil.disk_usage(path)
    return round(used / total * 100), total, used


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f}{unit}"
        n /= 1024


def main():
    ap = argparse.ArgumentParser(description="Alert when a disk crosses a usage threshold.")
    ap.add_argument("-t", "--threshold", type=int, default=85, help="percent, default 85")
    ap.add_argument("paths", nargs="*", default=["/", "/var"], help="mount points to check")
    args = ap.parse_args()

    host = socket.gethostname()
    alerted = False
    for path in args.paths:
        try:
            used, total, used_bytes = pct_used(path)
        except FileNotFoundError:
            print(f"[skip] {path} not found")
            continue
        status = "ALERT" if used >= args.threshold else "OK"
        if used >= args.threshold:
            alerted = True
        print(f"[{status}] {host}:{path} {used}% used "
              f"({human(used_bytes)} of {human(total)})")

    sys.exit(1 if alerted else 0)


if __name__ == "__main__":
    main()
```
