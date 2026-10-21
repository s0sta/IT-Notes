---
id: p576
title: "A file descriptor leak finder"
slug: a-file-descriptor-leak-finder
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, SRE, Performance, Troubleshooting]
source: "LinkedIn post P576 · PythonFixes series"
linkedin_date: 2030-06-02
design: code
script: fd_leak.py
---

# A file descriptor leak finder

A worker handles 200 requests a minute, then 20 after two days, then none. CPU and memory look ordinary, the network is fine, and the process is holding 1,012 descriptors against a limit of 1,024.

## Quick reference

The full script is at the end of this note: `fd_leak.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json
```

**Example output**

```text
FINDING 1/4 grew by 10+ fds
ALERT pid 4300 +172 fds, 1024 in 2 min
```

## Explained

### What it does

`fd_leak.py` reads two JSON snapshots, each a map of pid to fd count, taken `--interval` seconds apart. It ranks the growth, flags any process that gained `--min-growth` or more, and projects when it reaches `--limit`.

### What the screen shows

The fourteen lines load both snapshots, diff the pids they share, sort by growth, keep the ones over ten, then project the worst against 1024. On the dirty fixture: FINDING 1/4 grew by 10+ fds and ALERT pid 4300 +172 fds, 1024 in 2 min.

### How to run it

Take the samples with `ls /proc/PID/fd | wc -l` in a loop, then `python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json`. Exit 0 is no leak, 1 is a finding, 2 is bad input.

### The fix

Find the unclosed handle: `lsof -p 4300` lists every descriptor the process holds, and the last ones are the ones it forgot. In Python, a with block or try/finally around every open() closes the path that leaks.

### Prevention

Alert on fd growth per process, and set LimitNOFILE on purpose. The default soft limit is often 1024, which is small for a busy server.

> **The honest caveat:** a high count is not a leak. Only growth between two samples is.

> **The lesson:** count the handles, not the CPU. A leak looks like a slow machine until the limit is reached.

## In one line

> **Count the handles, not the CPU.** A leak looks like a slow machine until the limit is reached.

**Count one pid**

```bash
ls /proc/4300/fd | wc -l
```

## Script: fd_leak.py

Download: [scripts/fd_leak.py](../scripts/fd_leak.py)

```python
#!/usr/bin/env python3
"""fd_leak.py - find the process that is leaking file descriptors.

Reads two snapshots of file-descriptor counts, each a JSON object that
maps a pid to the number of entries in /proc/<pid>/fd, and ranks the
processes by growth. A process that gained --min-growth or more between
the samples is a finding, and the report projects when it reaches the
descriptor limit.

Take the two samples --interval seconds apart with
ls /proc/<pid>/fd | wc -l (as root, so every pid is readable) and write
one JSON object per sample:

    python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json --interval 60

Usage:
    python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json
    python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json --min-growth 20
    python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json --limit 65536 --interval 300
    python3 fd_leak.py --help

CI (fail a soak test that leaks descriptors):
    python3 fd_leak.py /tmp/fd-a.json /tmp/fd-b.json || exit 1

Cron (compare this hour with the one before):
    5 * * * * python3 /opt/s0sta/fd_leak.py /var/lib/s0sta/fd-1.json /var/lib/s0sta/fd-0.json

Exit codes: 0 no process grew by --min-growth, 1 at least one did,
2 usage error or unreadable, invalid or shapeless input.

Read-only: opens the two JSON files, compares the numbers and prints. It
never reads /proc itself, writes nothing and makes no network call.

A high fd count is not a leak; growth between two samples taken at a known
interval is. Count the second sample against the same limit the process
actually runs with: `ulimit -n` in its shell, or LimitNOFILE in the unit.

By s0sta.com
"""
import argparse
import json
import sys

DEFAULT_MIN = 10
DEFAULT_LIMIT = 1024
DEFAULT_INTERVAL = 60


class InputError(Exception):
    """An input that cannot be read."""


def read_snapshot(path):
    """Return {pid: fd_count} from one JSON snapshot, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise InputError("%s must be a JSON object of pid -> count" % path)
    if not doc:
        raise InputError("%s is an empty snapshot" % path)
    snapshot = {}
    for pid, count in doc.items():
        key = str(pid).strip()
        if not key.isdigit():
            raise InputError("%s: %r is not a pid" % (path, pid))
        if isinstance(count, bool) or not isinstance(count, int):
            raise InputError("%s: pid %s has a non-integer count" % (path, key))
        if count < 0:
            raise InputError("%s: pid %s has a negative count" % (path, key))
        snapshot[int(key)] = count
    return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank file-descriptor growth between two snapshots "
                    "(read-only).")
    parser.add_argument("first", help="earlier snapshot: JSON pid -> count")
    parser.add_argument("second", help="later snapshot: JSON pid -> count")
    parser.add_argument(
        "--min-growth", type=int, default=DEFAULT_MIN, metavar="N",
        help="flag a process that gained at least N fds (default: %d)"
             % DEFAULT_MIN)
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT, metavar="N",
        help="descriptor limit to project against (default: %d)" % DEFAULT_LIMIT)
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL, metavar="SECONDS",
        help="seconds between the two samples (default: %d)" % DEFAULT_INTERVAL)
    args = parser.parse_args(argv)

    if args.min_growth < 1:
        parser.error("--min-growth must be at least 1")
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.interval < 1:
        parser.error("--interval must be at least 1")

    try:
        before = read_snapshot(args.first)
        after = read_snapshot(args.second)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    common = sorted(set(before) & set(after))
    if not common:
        print("ERROR the two snapshots share no pid", file=sys.stderr)
        return 2

    growth = sorted(((after[pid] - before[pid], pid) for pid in common),
                    key=lambda item: (-item[0], item[1]))
    fresh = sorted(set(after) - set(before))
    gone = len(set(before) - set(after))

    for grown, pid in growth[:10]:
        if grown <= 0:
            continue
        print("GROWTH %d %d -> %d (%+d in %ds)"
              % (pid, before[pid], after[pid], grown, args.interval))
    if fresh:
        print("NEW    %d process(es) not in the first snapshot" % len(fresh))
    if gone:
        print("GONE   %d process(es) not in the second snapshot" % gone)

    leaks = [(grown, pid) for grown, pid in growth if grown >= args.min_growth]
    if not leaks:
        print("OK    no process grew by %d or more fds in %ds (%d compared)"
              % (args.min_growth, args.interval, len(common)))
        return 0

    print("FINDING %d/%d grew by %d+ fds"
          % (len(leaks), len(common), args.min_growth))
    for grown, pid in leaks[:5]:
        left = args.limit - after[pid]
        if left <= 0:
            print("ALERT pid %d +%d fds, %d now"
                  % (pid, grown, args.limit))
            continue
        per_minute = grown * 60.0 / args.interval
        minutes = int(left / per_minute)
        print("ALERT pid %d +%d fds, %d in %d min"
              % (pid, grown, args.limit, minutes))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
