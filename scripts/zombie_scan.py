#!/usr/bin/env python3
"""zombie_scan.py - find zombie processes and the parents that keep them.

Reads the output of `ps -eo pid,ppid,stat,comm` (a file or stdin), finds
every process whose state starts with Z, groups the dead children by
parent, and reports the parents that hold the most.

    ps -eo pid,ppid,stat,comm > /tmp/ps.txt
    python3 zombie_scan.py /tmp/ps.txt
    ps -eo pid,ppid,stat,comm | python3 zombie_scan.py

A parent at or above --max-per-parent (default 3) is printed as a PARENT
finding with the command that nudges it to reap. Every zombie is a
finding, so the exit code is 1 whenever one is present.

Usage:
    python3 zombie_scan.py /tmp/ps.txt
    python3 zombie_scan.py /tmp/ps.txt --max-per-parent 1
    ps -eo pid,ppid,stat,comm | python3 zombie_scan.py -
    python3 zombie_scan.py --help

CI (fail a soak test that leaks child processes):
    python3 zombie_scan.py /tmp/ps.txt || exit 1

Cron (a five-minute sweep on a busy worker):
    */5 * * * * ps -eo pid,ppid,stat,comm > /tmp/ps.txt && python3 /opt/s0sta/zombie_scan.py /tmp/ps.txt

Exit codes: 0 no zombie process, 1 at least one zombie, 2 usage error or
unreadable, empty or row-free input.

Read-only: opens the given file, parses text and prints a suggested
command. It never signals a process, writes nothing and makes no network
call.

A zombie holds a pid and a process table slot, not memory. Only its
parent can reap it, so the parent is the finding. A zombie whose parent
is pid 1 is normally transient: init reaps it on the next pass.

By s0sta.com
"""
import argparse
import sys
from collections import Counter, defaultdict

DEFAULT_MAX = 3


class InputError(Exception):
    """An input that cannot be read."""


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


def parse(text):
    """Return (rows, zombies) with zombies as (pid, ppid, stat, comm)."""
    rows, zombies = {}, []
    for number, raw in enumerate(text.splitlines(), start=1):
        fields = raw.split()
        if not fields or not fields[0].isdigit():
            continue          # header, banner, or a wrapped line
        if len(fields) < 4:
            raise InputError(
                "line %d is not a ps row: %s" % (number, raw.strip()))
        pid, ppid, stat = int(fields[0]), int(fields[1]), fields[2]
        comm = " ".join(fields[3:])
        rows[pid] = comm
        if stat[:1].upper() == "Z":
            zombies.append((pid, ppid, stat, comm))
    if not rows:
        raise InputError("no ps row found: is this ps -eo pid,ppid,stat,comm?")
    return rows, zombies


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Find zombie processes and the parents that keep them "
                    "(read-only).")
    parser.add_argument(
        "source", nargs="?", default="-",
        help="ps -eo pid,ppid,stat,comm output, or - for stdin (default: -)")
    parser.add_argument(
        "--max-per-parent", type=int, default=DEFAULT_MAX, metavar="N",
        help="flag a parent with at least this many zombies (default: %d)"
             % DEFAULT_MAX)
    args = parser.parse_args(argv)

    if args.max_per_parent < 1:
        parser.error("--max-per-parent must be at least 1")

    try:
        rows, zombies = parse(read_text(args.source))
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    if not zombies:
        print("OK    no zombie in %d processes" % len(rows))
        return 0

    for pid, ppid, stat, comm in zombies:
        print("ZOMBIE pid %d ppid %d %s %s" % (pid, ppid, stat, comm))

    groups = defaultdict(list)
    for pid, ppid, stat, comm in zombies:
        groups[ppid].append(pid)
    counts = Counter({ppid: len(pids) for ppid, pids in groups.items()})
    flagged = 0
    for ppid, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        if count < args.max_per_parent:
            continue
        flagged += 1
        name = rows.get(ppid)
        label = "PARENT %d (%s)" % (ppid, name) if name else "PARENT %d" % ppid
        print("%s holds %d zombies" % (label, count))
        print("SUGGEST kill -CHLD %d   # or restart it to clear the children"
              % ppid)

    orphans = sum(1 for _pid, ppid, _stat, _comm in zombies if ppid == 1)
    if orphans:
        print("NOTE  %d zombie(s) under pid 1: transient unless they persist"
              % orphans, file=sys.stderr)
    if not flagged:
        print("NOTE  no parent at or above %d zombies" % args.max_per_parent,
              file=sys.stderr)

    worst = min(counts, key=lambda ppid: (-counts[ppid], ppid))
    print("FINDING %d zombies in %d parents" % (len(zombies), len(counts)))
    print("ALERT parent %d holds %d zombies" % (worst, counts[worst]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
