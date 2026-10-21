#!/usr/bin/env python3
"""table_growth.py - compare two table-size snapshots and flag growth.

Reads two CSV snapshots of table sizes and compares them. The older date is
the baseline and the newer one is today. A table is flagged when it grew by
more than --percent or when its current size is over --max-gb. Rows with the
same table are summed, so a partition-level export works without a pivot.

CSV shape (header required, column order free):

    date,table,bytes
    2026-09-01,orders,6442450944
    2026-09-01,users,2147483648

Each file must hold one date. Bytes are decimal; thousands separators are
accepted. A table that is new in the later snapshot is reported as NEW and
only the size rule applies, because a percentage from zero is not a number.

Usage:
    python3 table_growth.py old.csv new.csv
    python3 table_growth.py old.csv new.csv --percent 50 --max-gb 20
    python3 table_growth.py --help

CI (fail the job when a table outgrows its budget):
    python3 table_growth.py /tmp/old.csv /tmp/new.csv --max-gb 50 || exit 1

Cron (weekly report from two size exports):
    0 6 * * 1 python3 /opt/s0sta/table_growth.py /var/lib/s0sta/last.csv /var/lib/s0sta/now.csv

Exit codes: 0 no table is over a threshold, 1 at least one flag,
2 usage, unreadable CSV or a row that does not match the shape.

Read-only: both files are opened for reading only. Nothing is written to a
database, and no query, vacuum or resize is run.

By s0sta.com
"""
import argparse
import csv
import sys
from datetime import date

COLUMNS = {"date", "table", "bytes"}
GIB = 1024.0 ** 3


def load_snapshot(path):
    """Return (snapshot_date, {table: bytes}); raise ValueError on bad input."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            if len(fields) != 3 or set(fields) != COLUMNS:
                raise ValueError("%s: header must be date,table,bytes" % path)
            rows = list(reader)
    except (OSError, UnicodeError) as exc:
        raise ValueError("%s: %s" % (path, exc))
    if not rows:
        raise ValueError("%s: no data rows" % path)

    sizes = {}
    found = None
    for index, row in enumerate(rows):
        where = "%s line %d" % (path, index + 2)
        raw_date = (row.get("date") or "").strip()
        try:
            day = date.fromisoformat(raw_date)
        except ValueError:
            raise ValueError("%s: bad date %r" % (where, raw_date))
        if found is None:
            found = day
        elif day != found:
            raise ValueError("%s: more than one date in the file" % where)
        table = (row.get("table") or "").strip()
        if not table:
            raise ValueError("%s: empty table name" % where)
        raw_bytes = (row.get("bytes") or "").strip().replace(",", "")
        try:
            value = int(raw_bytes)
        except ValueError:
            raise ValueError("%s: bad byte count %r" % (where, raw_bytes))
        if value < 0:
            raise ValueError("%s: negative byte count" % where)
        sizes[table] = sizes.get(table, 0) + value
    return found, sizes


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Compare two table-size snapshots and flag growth.")
    parser.add_argument("old", help="earlier snapshot CSV")
    parser.add_argument("new", help="later snapshot CSV")
    parser.add_argument("--percent", type=float, default=30.0,
                        help="flag growth above this percent (default 30)")
    parser.add_argument("--max-gb", type=float, default=10.0,
                        help="flag tables larger than this in GB (default 10)")
    args = parser.parse_args(argv)
    if args.percent < 0:
        parser.error("--percent must be zero or more")
    if args.max_gb <= 0:
        parser.error("--max-gb must be greater than zero")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        old_date, old = load_snapshot(args.old)
        new_date, new = load_snapshot(args.new)
    except ValueError as exc:
        print("table_growth: %s" % exc, file=sys.stderr)
        return 2
    if old_date == new_date:
        print("table_growth: both snapshots are dated %s" % old_date,
              file=sys.stderr)
        return 2
    if old_date > new_date:
        old_date, new_date = new_date, old_date
        old, new = new, old

    max_bytes = args.max_gb * GIB
    flags = 0
    print("GROWTH %s -> %s" % (old_date, new_date))
    for table in sorted(new, key=lambda name: (-new[name], name)):
        now = new[table]
        was = old.get(table, 0)
        gib = now / GIB
        if was == 0:
            print("NEW %s %.1f GiB" % (table, gib))
            if now > max_bytes:
                flags += 1
                print("FLAG %s %.1f GiB > %.1f GiB"
                      % (table, gib, args.max_gb))
            continue
        pct = (now - was) * 100.0 / was
        print("TABLE %s %.1f -> %.1f GiB %+.1f%%"
              % (table, was / GIB, gib, pct))
        if pct > args.percent:
            flags += 1
            print("FLAG %s growth %+.1f%% > %.1f%%"
                  % (table, pct, args.percent))
        if now > max_bytes:
            flags += 1
            print("FLAG %s %.1f GiB > %.1f GiB" % (table, gib, args.max_gb))

    delta = (sum(new.values()) - sum(old.values())) / GIB
    print("SUMMARY %d tables, %+.1f GiB, %d flags"
          % (len(new), delta, flags))
    if flags:
        print("SUGGEST review the writer for the flagged table, then archive or partition it")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
