#!/usr/bin/env python3
"""log_retention.py - find stale logs and over-volume directories in a listing.

Reads a CSV listing of log files (path, bytes, modified), groups it by
directory, and flags every file older than --max-days and every directory
whose total size is over --max-gb. Nothing is rotated, compressed or
deleted; the report names what a retention policy would act on.

CSV shape (header required, column order free):

    path,bytes,modified
    /var/log/nginx/access.log,1048576,2026-10-20T09:00:00Z
    /var/log/api/app.log,2048,2026-08-01

modified accepts YYYY-MM-DD or an ISO 8601 timestamp; a trailing Z is
accepted and a value without a timezone is treated as UTC. A duplicate
path is an input error, because a listing that counts one file twice would
double the directory volume.

Usage:
    python3 log_retention.py listing.csv
    python3 log_retention.py listing.csv --max-days 14 --max-gb 5
    python3 log_retention.py listing.csv --now 2026-10-21T00:00:00Z
    python3 log_retention.py --help

CI (fail the job when the volume or the age crosses the policy):
    python3 log_retention.py /tmp/logs.csv --max-days 30 --max-gb 20 || exit 1

Cron (weekly retention report):
    0 6 * * 1 find /var/log -type f -printf '%p,%s,%TY-%Tm-%Td\\n' > /tmp/logs.csv && python3 /opt/s0sta/log_retention.py /tmp/logs.csv

Exit codes: 0 no stale file and no directory over the volume, 1 at least
one finding, 2 usage, unreadable CSV or a row that does not match the shape.

Read-only: the listing is opened for reading only. No log is deleted,
truncated, compressed or moved; the find command printed at the end is a
suggestion for a human.

By s0sta.com
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta, timezone

GIB = 1024.0 ** 3
MIB = 1024.0 ** 2
COLUMNS = {"path", "bytes", "modified"}


def parse_time(text, where):
    """Parse an ISO 8601 timestamp; a naive value is treated as UTC."""
    raw = text.strip()
    if not raw:
        raise ValueError("%s: modified is empty" % where)
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        raise ValueError("%s: bad timestamp %r" % (where, text))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def load_listing(path):
    """Return the validated file rows, or raise ValueError."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            if len(fields) != 3 or set(fields) != COLUMNS:
                raise ValueError("%s: header must be path,bytes,modified"
                                 % path)
            rows = list(reader)
    except (OSError, UnicodeError) as exc:
        raise ValueError("%s: %s" % (path, exc))
    if not rows:
        raise ValueError("%s: no data rows" % path)

    seen = set()
    files = []
    for index, row in enumerate(rows):
        where = "%s line %d" % (path, index + 2)
        name = (row.get("path") or "").strip()
        if not name:
            raise ValueError("%s: empty path" % where)
        if name in seen:
            raise ValueError("%s: duplicate path %s" % (where, name))
        seen.add(name)
        raw_bytes = (row.get("bytes") or "").strip().replace(",", "")
        try:
            size = int(raw_bytes)
        except ValueError:
            raise ValueError("%s: bad byte count %r" % (where, raw_bytes))
        if size < 0:
            raise ValueError("%s: negative byte count" % where)
        modified = parse_time(row.get("modified") or "", where)
        files.append({"path": name, "bytes": size, "modified": modified})
    return files


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Flag stale logs and oversized directories.")
    parser.add_argument("listing", help="CSV listing of path,bytes,modified")
    parser.add_argument("--max-days", type=int, default=30,
                        help="flag files older than this (default 30)")
    parser.add_argument("--max-gb", type=float, default=10.0,
                        help="flag directories larger than this (default 10)")
    parser.add_argument("--now",
                        help="ISO 8601 reference time for the report")
    args = parser.parse_args(argv)
    if args.max_days < 0:
        parser.error("--max-days must be zero or more")
    if args.max_gb <= 0:
        parser.error("--max-gb must be greater than zero")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        files = load_listing(args.listing)
        as_of = parse_time(args.now, "--now") if args.now else \
            datetime.now(timezone.utc)
    except ValueError as exc:
        print("log_retention: %s" % exc, file=sys.stderr)
        return 2

    cutoff = as_of - timedelta(days=args.max_days)
    dirs = {}
    stale = []
    for item in files:
        directory = os.path.dirname(item["path"]) or "."
        age = max(0, (as_of - item["modified"]).days)
        info = dirs.setdefault(directory,
                               {"bytes": 0, "files": 0, "stale": 0})
        info["bytes"] += item["bytes"]
        info["files"] += 1
        if item["modified"] < cutoff:
            info["stale"] += 1
            stale.append((age, item))
    max_bytes = args.max_gb * GIB
    over = [name for name in dirs if dirs[name]["bytes"] > max_bytes]

    for name in sorted(dirs, key=lambda key: (-dirs[key]["bytes"], key)):
        info = dirs[name]
        word = "file" if info["files"] == 1 else "files"
        print("DIR %s %.1f GiB %d %s %d stale"
              % (name, info["bytes"] / GIB, info["files"], word,
                 info["stale"]))
    for name in sorted(over):
        print("OVER %s %.1f GiB > %.1f GiB"
              % (name, dirs[name]["bytes"] / GIB, args.max_gb))
    for age, item in sorted(stale, key=lambda row: (-row[0], row[1]["path"])):
        print("STALE %s %dd %.1f MiB"
              % (item["path"], age, item["bytes"] / MIB))

    total = sum(info["bytes"] for info in dirs.values()) / GIB
    print("TOTAL %d dirs %.1f GiB, %d stale, %d over"
          % (len(dirs), total, len(stale), len(over)))
    if stale or over:
        target = max(dirs, key=lambda key: (dirs[key]["stale"],
                                            dirs[key]["bytes"]))
        if stale:
            print("SUGGEST find %s -type f -mtime +%d -print"
                  % (target, args.max_days))
        else:
            print("SUGGEST du -sh %s/* | sort -h | tail" % target)
        return 1
    print("OK no stale logs, no directory over %.1f GiB" % args.max_gb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
