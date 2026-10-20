---
id: p330
title: "A slow-query log report in Python"
slug: a-slow-query-log-report-in-python
sections: [it]
topic: "Python scripts"
tags: [SQL, PostgreSQL, Python, Logging, Performance]
source: "LinkedIn post P330 · Data series"
linkedin_date: 2028-11-05
design: code
script: slow_query_report.py
---

# A slow-query log report in Python

The pager goes off at 02:00 because the checkout is slow, and the dashboard shows a flat line. The database log has been recording every slow statement for weeks.

## Quick reference

The full script is at the end of this note: **slow_query_report.py** (standard library only, no `pip install`).

**Run it**

```bash
python3 slow_query_report.py postgres.log
```

**Example output**

```text
1800.000 ms  SELECT * FROM orders WHERE total > 100
SLOW 2 of 5
```

## Explained

**What it reads**  
The script scans a PostgreSQL log for lines containing duration: 1234.567 ms. It takes the number after duration:, strips the statement: or execute \<unnamed>: prefix that follows, and keeps the text. Lines without a duration are skipped, and parse and bind lines are ignored because they are steps, not query executions.

**What it ranks**  
Each statement becomes a row of milliseconds and text. The report sorts them slowest first, prints the slowest rows, and counts how many crossed the threshold. The exit code is 1 when at least one statement is over it, so a CI job fails on the same evidence you would read.

**How to run it**  
`python3 slow_query_report.py postgres.log --threshold 1000` prints the report. The threshold defaults to 1000 ms; `--top` changes the list length and `--json` prints one object for a dashboard. Exit 2 means the file could not be read or the arguments were wrong, which is a broken check, not a clean log.

> **The honest caveat:** the report only sees what the log wrote. log_min_duration_statement filters at the server, and a statement containing newlines is written across several lines, of which the script reads only the first.

> **The lesson:** the slow query is usually already in the log, waiting for someone to rank it.

## In one line

> **The log knows what dashboards hide.** The log already has the evidence; the report just ranks it.

**Rank the log**

```bash
python3 slow_query_report.py postgres.log
```

## Script: slow_query_report.py

Download: [scripts/slow_query_report.py](../scripts/slow_query_report.py)

```python
#!/usr/bin/env python3
"""slow_query_report.py - rank slow statements in a PostgreSQL log.

Scans a PostgreSQL server log for lines containing "duration: 1234.567 ms",
keeps the statement text after "statement:" or "execute ...:", ranks the
slowest statements and exits 1 when one is over --threshold.

Read-only: it reads a log file (or stdin with "-") and writes nothing.

Exit codes: 0 no statement over the threshold, 1 at least one statement over
it, 2 usage or input error.

Usage:
    python3 slow_query_report.py postgresql.log
    python3 slow_query_report.py postgresql.log --threshold 500 --top 20
    tail -n 5000 postgresql.log | python3 slow_query_report.py -
    python3 slow_query_report.py postgresql.log --json

Cron or CI, fail the job when a slow statement appears:
    python3 slow_query_report.py /var/log/postgresql/postgresql.log || exit 1

By s0sta.com
"""
import argparse
import json
import re
import sys

DURATION_RE = re.compile(r"duration:\s*([0-9]+(?:\.[0-9]+)?)\s*ms\b", re.IGNORECASE)
MAX_STATEMENT = 110


class ReportError(Exception):
    """Anything that should end the run with exit code 2."""


def statement_after(line, match):
    """The statement text after a duration match, or None for parse/bind lines."""
    rest = line[match.end():].strip()
    if not rest:
        return None
    low = rest.lower()
    if low.startswith("statement:"):
        return rest[len("statement:"):].strip() or None
    if low.startswith("execute "):
        if ":" not in rest:
            return None
        return rest.split(":", 1)[1].strip() or None
    return None


def parse_lines(lines):
    """Every (duration_ms, statement) pair in an iterable of log lines."""
    rows = []
    for line in lines:
        match = DURATION_RE.search(line)
        if not match:
            continue
        stmt = statement_after(line, match)
        if stmt is None:
            continue
        rows.append((float(match.group(1)), " ".join(stmt.split())))
    return rows


def read_rows(path):
    """Read the log file (or stdin for "-") and return the duration rows."""
    try:
        if path == "-":
            return parse_lines(sys.stdin)
        with open(path, encoding="utf-8", errors="replace") as fh:
            return parse_lines(fh)
    except OSError as exc:
        raise ReportError("cannot read %s: %s" % (path, exc))


def build_report(path, rows, threshold, top):
    """The report dictionary, ready for text or JSON output."""
    ranked = sorted(rows, key=lambda row: -row[0])[:top]
    over = [row for row in rows if row[0] > threshold]
    slowest = max((row[0] for row in rows), default=0.0)
    return {
        "file": path,
        "threshold_ms": threshold,
        "statements": len(rows),
        "over": len(over),
        "slowest_ms": slowest,
        "top": [{"duration_ms": ms, "statement": stmt} for ms, stmt in ranked],
        "ok": not over,
    }


def print_report(rep):
    """The human-readable report."""
    print("SLOW QUERY REPORT  %s" % rep["file"])
    print("threshold %.3f ms | %d statements | %d over"
          % (rep["threshold_ms"], rep["statements"], rep["over"]))
    if rep["top"]:
        print("")
        print("%3s  %12s  %s" % ("#", "DURATION ms", "STATEMENT"))
        for i, item in enumerate(rep["top"], 1):
            stmt = item["statement"]
            if len(stmt) > MAX_STATEMENT:
                stmt = stmt[:MAX_STATEMENT - 3] + "..."
            print("%3d  %12.3f  %s" % (i, item["duration_ms"], stmt))
        print("")
    if rep["ok"]:
        print("OK %d statements, none over %.3f ms"
              % (rep["statements"], rep["threshold_ms"]))
    else:
        print("ALERT %d statements over %.3f ms"
              % (rep["over"], rep["threshold_ms"]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank the slowest statements in a PostgreSQL log.",
        epilog="Exit codes: 0 clean, 1 slow statement, 2 usage or input error.")
    parser.add_argument("logfile", nargs="?", default="-",
                        help="log file to read, or - for stdin (default -)")
    parser.add_argument("--threshold", type=float, default=1000.0, metavar="MS",
                        help="flag statements over this many milliseconds (default 1000)")
    parser.add_argument("--top", type=int, default=10, metavar="N",
                        help="rows to print (default 10)")
    parser.add_argument("--json", action="store_true", help="print one JSON report")
    args = parser.parse_args(argv)

    if args.threshold < 0:
        parser.error("--threshold must be zero or positive")
    if args.top < 1:
        parser.error("--top must be at least 1")
    try:
        rows = read_rows(args.logfile)
    except ReportError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2
    rep = build_report(args.logfile, rows, args.threshold, args.top)
    if args.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
    else:
        print_report(rep)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
```
