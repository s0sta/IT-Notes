---
id: p350
title: "A table size report in Python"
slug: a-table-size-report-in-python
sections: [it]
topic: "Python scripts"
tags: [PostgreSQL, Python, DatabasePerformance, Observability, SRE]
source: "LinkedIn post P350 · Data series"
linkedin_date: 2028-12-21
design: code
script: table_sizes.py
---

# A table size report in Python

The table is eight hundred megabytes and the indexes are one point two gigabytes, which nobody noticed until the restore took an hour. Size is the cheapest performance fact to collect.

## Quick reference

The full script is at the end of this note: `table_sizes.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 table_sizes.py sizes.csv 1.0
```

**Example output**

```text
audit_log        50.0  150.0
TOTAL 1726.0 MB, 1 over
```

## Explained

**What it reads**  
A CSV with relname, table_bytes and index_bytes, straight from `psql --csv`. pg_table_size counts the table's heap plus TOAST, the free space map and the visibility map, and pg_indexes_size counts every index attached to it. Both numbers are bytes on disk, not row counts.

**What it prints**  
One row per table, largest total first: table megabytes, index megabytes, the ratio between them, and a state. The summary adds the grand total and names every table over the ratio.

**The threshold**  
The second argument is the ratio; the attached script exposes it as `--ratio` and defaults to 1.0, so an index bigger than its table is reported. `--min-mb`, default 1, keeps an eight kilobyte table with a sixteen kilobyte index out of the report. Exit 1 when anything is flagged.

> **The honest caveat:** a large index can be correct. A covering index on a narrow table, or a primary key on a UUID column, is big by design, so the ratio is a prompt to look rather than a verdict.

> **The lesson:** an index is a second copy of the data, and you pay for it on every write and every restore.

## In one line

> **An index bigger than its table.** That is not speed, that is a second copy with overhead.

**Export the sizes**

```bash
psql --csv -c 'SELECT relname ...'
```

## Script: table_sizes.py

Download: [scripts/table_sizes.py](../scripts/table_sizes.py)

```python
#!/usr/bin/env python3
"""table_sizes.py - rank table and index sizes, and flag index overhead.

Reads a CSV with the columns relname, table_bytes and index_bytes, as produced
by:

    psql --csv -c "SELECT relname, pg_table_size(oid) AS table_bytes, pg_indexes_size(oid) AS index_bytes FROM pg_class WHERE relkind = 'r' ORDER BY 2 DESC" > sizes.csv

Blank size cells count as zero. For every table it prints the table size, the
index size and the index ratio
(index bytes divided by table bytes), largest total first. A table is flagged
when its indexes are larger than --ratio times the table (default 1.0). Tables
below --min-mb (default 1) are left out of the flagging, so an 8 kB table with
one index does not win the report. Exit code 1 when anything is flagged.

Read-only: it reads a CSV and prints a report. It never connects to a database.
Exit codes: 0 nothing over the ratio, 1 at least one table over it, 2 usage or
input error.

Usage:
    psql --csv -c "SELECT relname, pg_table_size(oid) AS table_bytes, pg_indexes_size(oid) AS index_bytes FROM pg_class WHERE relkind = 'r'" > sizes.csv
    python3 table_sizes.py sizes.csv
    python3 table_sizes.py sizes.csv --ratio 0.5 --min-mb 10
    python3 table_sizes.py sizes.csv --top 10 --json

Cron (weekly size review, Monday 07:00):
    0 7 * * 1 psql --csv -c "SELECT relname, pg_table_size(oid) AS table_bytes, pg_indexes_size(oid) AS index_bytes FROM pg_class WHERE relkind = 'r'" > /tmp/sizes.csv && python3 table_sizes.py /tmp/sizes.csv --ratio 1.0 >> /var/log/table_sizes.log 2>&1

CI gate (fails when an index is bigger than its table):
    python3 table_sizes.py sizes.csv --ratio 1.0

By s0sta.com
"""
import argparse
import csv
import json
import sys

FIELDS = ("relname", "table_bytes", "index_bytes")
MIB = 1024.0 * 1024.0


def as_bytes(value):
    """An integer byte count, or None when the cell is blank."""
    text = (value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        number = int(text)
    except ValueError:
        return "bad"
    return number if number >= 0 else "bad"


def read_rows(handle, label, errors):
    """Table rows from one CSV handle, with the three required columns."""
    reader = csv.DictReader(handle)
    missing = [name for name in FIELDS if name not in (reader.fieldnames or [])]
    if missing:
        errors.append("%s: missing column(s): %s" % (label, ", ".join(missing)))
        return []
    rows = []
    for lineno, record in enumerate(reader, 2):
        name = (record.get("relname") or "").strip()
        table = as_bytes(record.get("table_bytes"))
        index = as_bytes(record.get("index_bytes"))
        if not name:
            errors.append("%s:%d: empty relname" % (label, lineno))
            continue
        if table == "bad" or index == "bad":
            errors.append("%s:%d: table_bytes and index_bytes must be integers"
                          % (label, lineno))
            continue
        rows.append({"relname": name, "table": table or 0,
                     "index": index or 0})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank table and index sizes from a CSV and flag tables "
                    "whose indexes are larger than --ratio times the table.")
    parser.add_argument("path", metavar="PATH",
                        help="CSV with relname, table_bytes, index_bytes")
    parser.add_argument("--ratio", type=float, default=1.0, metavar="R",
                        help="flag when index bytes > R x table bytes (default 1.0)")
    parser.add_argument("--min-mb", type=float, default=1.0, metavar="MB",
                        help="ignore tables below this size for flagging (default 1)")
    parser.add_argument("--top", type=int, default=0, metavar="N",
                        help="print only the N largest tables (default all)")
    parser.add_argument("--json", action="store_true",
                        help="print one machine-readable JSON object")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="print the summary only, no table")
    args = parser.parse_args(argv)

    if args.ratio < 0:
        parser.error("--ratio cannot be negative")
    if args.min_mb < 0:
        parser.error("--min-mb cannot be negative")
    if args.top < 0:
        parser.error("--top cannot be negative")

    errors = []
    try:
        with open(args.path, "r", encoding="utf-8", newline="") as handle:
            rows = read_rows(handle, args.path, errors)
    except OSError as exc:
        errors.append("%s: %s" % (args.path, exc))
        rows = []

    for message in errors:
        print("error: %s" % message, file=sys.stderr)
    if errors:
        return 2
    if not rows:
        print("error: no table rows in %s" % args.path, file=sys.stderr)
        return 2

    floor = args.min_mb * MIB
    for row in rows:
        row["total"] = row["table"] + row["index"]
        row["ratio"] = row["index"] / float(row["table"]) if row["table"] else 0.0
        row["over"] = (row["index"] > args.ratio * row["table"]
                       and row["total"] >= floor)
    rows.sort(key=lambda item: (-item["total"], item["relname"]))
    shown = rows[:args.top] if args.top else rows
    over = [row for row in rows if row["over"]]
    grand = sum(row["total"] for row in rows)

    if args.json:
        print(json.dumps({
            "tables": len(rows),
            "total_bytes": grand,
            "ratio": args.ratio,
            "min_mb": args.min_mb,
            "over": len(over),
            "flagged": [row["relname"] for row in over],
            "rows": [{"relname": row["relname"],
                      "table_bytes": row["table"],
                      "index_bytes": row["index"],
                      "ratio": round(row["ratio"], 3),
                      "over": row["over"]} for row in shown],
        }, sort_keys=True))
        return 1 if over else 0

    if not args.quiet:
        print("%-24s %9s %9s %7s  %s"
              % ("TABLE", "TABLE_MB", "INDEX_MB", "RATIO", "STATE"))
        for row in shown:
            print("%-24s %9.1f %9.1f %7.2f  %s"
                  % (row["relname"][:24], row["table"] / MIB,
                     row["index"] / MIB, row["ratio"],
                     "OVER" if row["over"] else "ok"))
        print()
    print("TOTAL %.1f MB across %d table%s; %d over ratio %g"
          % (grand / MIB, len(rows), "" if len(rows) == 1 else "s",
             len(over), args.ratio))
    for row in over:
        print("OVER %s: %.1f MB of index on %.1f MB of table"
              % (row["relname"], row["index"] / MIB, row["table"] / MIB))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
```
