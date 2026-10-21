---
id: p572
title: "An inode exhaustion forecaster"
slug: an-inode-exhaustion-forecaster
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, SysAdmin, SRE, Troubleshooting]
source: "LinkedIn post P572 · PythonFixes series"
linkedin_date: 2030-05-23
design: code
script: inode_watch.py
---

# An inode exhaustion forecaster

At 03:10 a deploy host stops writing logs. `df -h` reports 41% free, every write returns ENOSPC, and the pager insists the disk is healthy. The bytes are there; the inodes are not.

## Quick reference

The full script is at the end of this note: `inode_watch.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 inode_watch.py /tmp/df_i.txt /tmp/inode_history.json
```

**Example output**

```text
FINDING 2 filesystems to watch
ALERT /var 96% 5d left, /srv/data 92% 29d left
```

## Explained

### What it does

`inode_watch.py` reads `df -i` output, compares each filesystem's IUse% with `--threshold (80` by default), and projects the fill from a growth history JSON: mount point to [epoch, used] samples. A filesystem under the threshold is still flagged when the projection lands inside `--horizon` days.

### What the screen shows

The fourteen lines read the df path and the history, filter rows at or above 80%, then print FINDING 2 filesystems to watch and ALERT `/var 96% 5d` left, `/srv/data 92% 29d` left.

### How to run it

`df -iP | python3 inode_watch.py` - `/var/lib/s0sta/inode_history.json`, or a captured file. Exit 0 is clean, 1 is a finding, 2 is bad input. It writes nothing, so cron and CI can run it.

### The fix

On `/var`, find what creates files and never removes them: PHP sessions, mail queues, container layers. `du --inodes -x --max-depth=1 /var | sort -n |` tail -5 names the directory that grew. Clean the producer, not the files.

### Prevention

Sample hourly and alert at 80%, not 95%. ext4 defaults to one inode per 16 KB and each inode costs 256 bytes, so a volume sized for large files can still run out of names.

> **The honest caveat:** two samples make a line, not a trend.

> **The lesson:** `df -h` measures bytes, and `df -i` measures the things that hold them.

## In one line

> **Free space is not free inodes.** `df -h` counts bytes. The filesystem also runs out of names.

**Project the fill**

```bash
df -iP | python3 inode_watch.py
```

## Script: inode_watch.py

Download: [scripts/inode_watch.py](../scripts/inode_watch.py)

```python
#!/usr/bin/env python3
"""inode_watch.py - forecast inode exhaustion from df -i output.

Reads the text of `df -i` (a file or stdin), flags every filesystem whose
IUse% is at or above a threshold, and projects when it fills from a growth
history JSON. A filesystem below the threshold is still reported when the
projection says it fills inside --horizon days.

The history file is a JSON object that maps a mount point to a list of
[epoch_seconds, used_inodes] samples, oldest first:

    {"/var": [[1761000000, 1258291], [1761028800, 1267000]]}

Write it from cron or a metrics agent; this script only reads it. The
projection is the average growth between the first and the last sample,
so a longer history gives a steadier slope than the last two points.

Usage:
    df -iP | python3 inode_watch.py
    python3 inode_watch.py /tmp/df_i.txt
    python3 inode_watch.py /tmp/df_i.txt /tmp/inode_history.json
    python3 inode_watch.py /tmp/df_i.txt /tmp/inode_history.json --threshold 90
    python3 inode_watch.py /tmp/df_i.txt /tmp/inode_history.json --horizon 7
    python3 inode_watch.py --help

CI (block a deploy onto a host near the inode limit):
    python3 inode_watch.py /var/lib/s0sta/df_i.txt /var/lib/s0sta/history.json || exit 1

Cron (hourly capture, one report per run):
    5 * * * * df -iP > /var/lib/s0sta/df_i.txt && python3 /opt/s0sta/inode_watch.py /var/lib/s0sta/df_i.txt /var/lib/s0sta/history.json

Exit codes: 0 no finding, 1 a filesystem is at or above the threshold or
fills inside --horizon days, 2 usage error or unreadable, empty or
unparseable input.

Read-only: opens the given files, parses text and prints. It writes
nothing, changes nothing and makes no network call.

Mount points that contain a space are printed by df as `\\040`; the report
keeps the escaped name. Rows that report `-` for inodes (NFS, some
overlay mounts) are skipped with a note on stderr.

By s0sta.com
"""
import argparse
import json
import sys

DEFAULT_THRESHOLD = 80
DEFAULT_HORIZON = 14.0


class InputError(Exception):
    """An input that cannot be audited."""


def read_text(source):
    """Return the whole input as text, or raise InputError."""
    try:
        if source == "-":
            text = sys.stdin.read()
        else:
            with open(source, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (source, exc.strerror or exc))
    if not text.strip():
        raise InputError("%s: empty input" % source)
    return text


def parse_df(text):
    """Return a list of row dicts from df -i output, or raise InputError."""
    rows, pending, skipped = [], None, 0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        fields = line.split()
        if fields[0].lower() == "filesystem":
            continue
        # A long device name is printed on its own line, then the row.
        if len(fields) == 1 and fields[0].startswith("/"):
            pending = fields[0]
            continue
        if pending and len(fields) == 5 and fields[0].isdigit():
            fields = [pending] + fields
            pending = None
        elif pending:
            pending = None
        if len(fields) < 6:
            raise InputError(
                "line %d is not a df -i row: %s" % (number, line))
        device, total, used, free, pct = fields[0], fields[1], fields[2], fields[3], fields[4]
        mount = " ".join(fields[5:])
        if pct == "-" or not (total.isdigit() and used.isdigit() and free.isdigit()):
            skipped += 1
            continue
        percent = int(pct.rstrip("%"))
        if int(total) <= 0:
            skipped += 1
            continue
        rows.append({
            "device": device,
            "mount": mount,
            "total": int(total),
            "used": int(used),
            "free": int(free),
            "percent": min(100, percent),
        })
    if not rows:
        raise InputError("no df -i row with an inode count")
    return rows, skipped


def load_history(path):
    """Read and validate the growth history JSON, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise InputError("%s must be a JSON object of mount -> samples" % path)
    history = {}
    for mount, samples in doc.items():
        if not isinstance(samples, list):
            raise InputError("%s: %s must be a list of samples" % (path, mount))
        pairs = []
        for item in samples:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise InputError(
                    "%s: %s needs [epoch, used] pairs" % (path, mount))
            stamp, used = item
            if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
                raise InputError(
                    "%s: %s has a non-numeric epoch" % (path, mount))
            if isinstance(used, bool) or not isinstance(used, (int, float)):
                raise InputError(
                    "%s: %s has a non-numeric inode count" % (path, mount))
            pairs.append((float(stamp), float(used)))
        pairs.sort()
        history[mount] = pairs
    return history


def project(samples, free):
    """Return (inodes_per_hour, days_left) or None when there is no slope."""
    if len(samples) < 2:
        return None
    (t0, u0), (t1, u1) = samples[0], samples[-1]
    hours = (t1 - t0) / 3600.0
    if hours <= 0 or u1 <= u0:
        return None
    rate = (u1 - u0) / hours
    return rate, free / rate / 24.0


def eta(forecast):
    """Return the short projection used in the one-line alert."""
    return "no data" if forecast is None else "%dd left" % forecast[1]


def report(rows, history, threshold, horizon):
    """Return (finding, lines) for every filesystem worth acting on."""
    hits = []
    for row in rows:
        forecast = project(history.get(row["mount"]) or [], row["free"])
        days = None if forecast is None else forecast[1]
        urgent = days is not None and days <= horizon
        if row["percent"] < threshold and not urgent:
            continue
        hits.append((row, forecast))
    if not hits:
        return False, ["OK    no filesystem at or above %d%% inodes, "
                       "nothing fills inside %gd" % (threshold, horizon)]
    lines = []
    for row, forecast in hits:
        if forecast is None:
            detail = "no growth history"
        else:
            detail = "fills in %dd at %d/h" % (forecast[1], forecast[0])
        lines.append("WARN  %-22s %3d%% used, %8d free, %s"
                     % (row["mount"], row["percent"], row["free"], detail))
    lines.append("FINDING %d filesystem%s to watch"
                 % (len(hits), "" if len(hits) == 1 else "s"))
    lines.append("ALERT " + ", ".join(
        "%s %d%% %s" % (row["mount"], row["percent"], eta(forecast))
        for row, forecast in hits))
    return True, lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Forecast inode exhaustion from df -i output (read-only).")
    parser.add_argument(
        "df", nargs="?", default="-",
        help="df -i output to read, or - for stdin (default: -)")
    parser.add_argument(
        "history", nargs="?", default=None,
        help="growth history JSON: mount -> [[epoch, used], ...]")
    parser.add_argument(
        "--threshold", type=int, default=DEFAULT_THRESHOLD, metavar="PCT",
        help="flag a filesystem at or above this inode use level, in percent (default: %d)"
             % DEFAULT_THRESHOLD)
    parser.add_argument(
        "--horizon", type=float, default=DEFAULT_HORIZON, metavar="DAYS",
        help="also flag a fill projected inside this many days (default: %g)"
             % DEFAULT_HORIZON)
    args = parser.parse_args(argv)

    if not 1 <= args.threshold <= 100:
        parser.error("--threshold must be between 1 and 100")
    if args.horizon < 0:
        parser.error("--horizon must not be negative")

    try:
        rows, skipped = parse_df(read_text(args.df))
        history = load_history(args.history) if args.history else {}
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    if skipped:
        print("NOTE %d row(s) skipped: no inode count" % skipped, file=sys.stderr)
    if not history and args.history is None:
        print("NOTE no history file: projection unavailable", file=sys.stderr)

    finding, lines = report(rows, history, args.threshold, args.horizon)
    for line in lines:
        print(line)
    return 1 if finding else 0


if __name__ == "__main__":
    sys.exit(main())
```
