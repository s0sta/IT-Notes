---
id: p345
title: "An index advisor in Python"
slug: an-index-advisor-in-python
sections: [it]
topic: "Python scripts"
tags: [PostgreSQL, Python, DatabasePerformance, QueryTuning, SQL]
source: "LinkedIn post P345 · Data series"
linkedin_date: 2028-12-10
design: code
script: index_advisor.py
---

# An index advisor in Python

Every slow query review starts the same way: someone reads a plan, spots a Seq Scan, and guesses an index. The guess is the part worth automating.

## Quick reference

The full script is at the end of this note: **index_advisor.py** (standard library only, no `pip install`).

**Run it**

```bash
python3 index_advisor.py plan.json --rows 250000
```

**Example output**

```text
CREATE INDEX ON orders (customer_id);
index_advisor: 1 candidate
```

## Explained

**What it reads**  
EXPLAIN (FORMAT JSON) returns a list with one object whose Plan is the root node. Each node has a Node Type and a Total Cost, plus a Relation Name and Filter where they apply, and children in Plans. Save the output with `psql -Atc`.

**What it finds**  
The script walks the tree with a stack. A node counts when its Node Type ends in Seq Scan, it names a relation, and it has a Filter. A small regular expression pulls column names out of the filter, skipping casts, and the columns become a CREATE INDEX line.

**The table size**  
A seq scan on 800 rows is the right plan. Pass `--rows` with the table's row count and the script skips candidates below `--min-rows`, default 1000, because an index there costs writes.

**Running it**  
Save one plan per file and pass several, or pipe psql output on stdin. Exit 0 means no candidate, 1 means at least one, and 2 means unreadable JSON or no Plan object.

> **The honest caveat:** a filter column is a candidate, not a verdict. A low-selectivity filter, a function around the column, or a table that fits in memory may still choose a seq scan. Build the index on a copy and read the second plan.

> **The lesson:** let the plan name the index, and let a second plan prove it.

## In one line

> **The plan tells you the index.** A seq scan on a large table with a filter is an index asking to exist.

**Plan json, saved**

```bash
psql -Atc 'EXPLAIN (FORMAT JSON) SELECT 1'
```

## Script: index_advisor.py

Download: [scripts/index_advisor.py](../scripts/index_advisor.py)

```python
#!/usr/bin/env python3
"""index_advisor.py - read EXPLAIN (FORMAT JSON) plans and suggest indexes.

The script reads one or more saved plans, for example:

    psql -Atc "EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE customer_id = 42" > plan.json

and walks every node of every plan. A node is a candidate when its "Node Type"
is a sequential scan (Seq Scan or Parallel Seq Scan), it has a "Relation Name",
and it carries a "Filter" - a condition evaluated after the scan. Columns named
in the filter are collected and printed as a suggested CREATE INDEX statement.
A function call around a column, such as lower(name), is reported as the column
name; a functional index is the real fix for that case.

--rows is the table size you are auditing, in rows. When it is given and the
table is below --min-rows (default 1000), the candidate is skipped: a small
table is usually cheaper to scan than to index.

Read-only: it reads JSON and prints suggestions. It never connects to a
database and never creates an index. Exit codes: 0 no candidate, 1 at least
one candidate, 2 usage or input error.

Usage:
    python3 index_advisor.py plan.json
    python3 index_advisor.py plan.json --rows 250000
    psql -Atc "EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE status = 'open'" | python3 index_advisor.py -
    python3 index_advisor.py a.json b.json --min-rows 5000 --json

Cron (weekly index review, Monday 06:00):
    0 6 * * 1 psql -Atc "EXPLAIN (FORMAT JSON) SELECT * FROM orders WHERE customer_id = 42" > /tmp/plan.json && python3 index_advisor.py /tmp/plan.json --rows 250000 >> /var/log/index_advisor.log 2>&1

CI gate (fails when a plan still scans a large table):
    python3 index_advisor.py plan.json --rows 250000

By s0sta.com
"""
import argparse
import json
import re
import sys

# A filter looks like "(customer_id = 42)" or "((status)::text = 'open'::text)".
# The lookbehind keeps the "text" of a cast from being read as a column name.
COL_RE = re.compile(
    r"(?<![:A-Za-z0-9_'\"])(?:\"([A-Za-z_][A-Za-z0-9_]*)\"|([A-Za-z_][A-Za-z0-9_]*))"
    r"\s*\)?\s*(?:::\s*[A-Za-z_][A-Za-z0-9_ ]*?)?"
    r"\s*(?:=|<>|!=|>=|<=|>|<|~~\*?|!~~\*?)"
)

STOP = {"and", "or", "not", "is", "null", "true", "false", "any", "all",
        "select", "where", "case", "when", "then", "else", "end"}


def columns_in(text):
    """Column names compared in a filter, unique, in order.

    Unquoted names are folded to lower case the way PostgreSQL folds them;
    a quoted identifier keeps its case and its quotes in the suggestion.
    """
    seen = []
    for match in COL_RE.finditer(text or ""):
        quoted, plain = match.group(1), match.group(2)
        name = quoted or plain
        if name.lower() in STOP or name.isdigit():
            continue
        name = '"%s"' % quoted if quoted else name.lower()
        if name not in seen:
            seen.append(name)
    return seen


def plan_roots(doc, label, errors):
    """Plan objects from one decoded EXPLAIN document."""
    if isinstance(doc, dict):
        doc = [doc]
    if not isinstance(doc, list):
        errors.append("%s: expected a JSON array or object" % label)
        return []
    roots = []
    for item in doc:
        if isinstance(item, dict) and isinstance(item.get("Plan"), dict):
            roots.append(item["Plan"])
        elif isinstance(item, dict) and "Node Type" in item:
            roots.append(item)
        else:
            errors.append("%s: no Plan object in the document" % label)
    return roots


def scan_node(node):
    """Candidates in one plan node and its children, depth first."""
    found = []
    stack = [node]
    while stack:
        current = stack.pop()
        if not isinstance(current, dict):
            continue
        kind = str(current.get("Node Type", ""))
        relation = current.get("Relation Name")
        condition = current.get("Filter")
        if kind in ("Seq Scan", "Parallel Seq Scan") and relation and condition:
            found.append({"relation": relation, "node": kind,
                          "filter": condition,
                          "columns": columns_in(condition)})
        children = current.get("Plans") or []
        stack.extend(reversed(children))
    return found


def read_document(path):
    """Decoded JSON from a path, or '-' for stdin."""
    if path == "-":
        return json.loads(sys.stdin.read())
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Suggest CREATE INDEX statements from EXPLAIN (FORMAT JSON) "
                    "plans that still use a sequential scan with a filter.")
    parser.add_argument("paths", nargs="*", default=["-"], metavar="PATH",
                        help="saved plan JSON file(s), or - for stdin (default)")
    parser.add_argument("--rows", type=int, default=None, metavar="N",
                        help="table size in rows; small tables are skipped")
    parser.add_argument("--min-rows", type=int, default=1000, metavar="N",
                        help="skip candidates below this size (default 1000)")
    parser.add_argument("--json", action="store_true",
                        help="print one machine-readable JSON object")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="print the summary only, no per-scan detail")
    args = parser.parse_args(argv)

    if args.rows is not None and args.rows < 0:
        parser.error("--rows cannot be negative")
    if args.min_rows < 0:
        parser.error("--min-rows cannot be negative")

    errors = []
    candidates = []
    for path in args.paths:
        label = "<stdin>" if path == "-" else path
        try:
            doc = read_document(path)
        except (OSError, ValueError) as exc:
            errors.append("%s: %s" % (label, exc))
            continue
        for root in plan_roots(doc, label, errors):
            candidates.extend(scan_node(root))

    for message in errors:
        print("error: %s" % message, file=sys.stderr)
    if errors:
        return 2

    unique = []
    seen = set()
    for item in candidates:
        key = (item["relation"], tuple(item["columns"]), item["filter"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    skipped = []
    if args.rows is not None:
        for item in list(unique):
            if args.rows < args.min_rows:
                unique.remove(item)
                skipped.append(item)

    if args.json:
        print(json.dumps({
            "rows": args.rows,
            "min_rows": args.min_rows,
            "count": len(unique),
            "skipped": [item["relation"] for item in skipped],
            "candidates": [{"relation": item["relation"],
                            "node": item["node"],
                            "filter": item["filter"],
                            "columns": item["columns"]} for item in unique],
        }, sort_keys=True))
        return 1 if unique else 0

    if not unique:
        for item in skipped:
            print("SKIP %s: %d rows is below %d, a seq scan is fine"
                  % (item["relation"], args.rows, args.min_rows))
        print("index_advisor: no seq scan with a filter to report")
        return 0

    width = max(len(item["relation"]) for item in unique)
    for item in unique:
        if not args.quiet:
            print("%-*s  %s" % (width, item["relation"], item["node"]))
            print("%-*s  filter  %s" % (width, "", item["filter"]))
        if item["columns"]:
            print("%-*s  CREATE INDEX ON %s (%s);"
                  % (width, "", item["relation"], ", ".join(item["columns"])))
        else:
            print("%-*s  no column parsed; review the filter by hand"
                  % (width, ""))
    print("index_advisor: %d candidate%s"
          % (len(unique), "" if len(unique) == 1 else "s"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
