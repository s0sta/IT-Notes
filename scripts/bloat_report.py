#!/usr/bin/env python3
"""Report PostgreSQL table bloat from a pg_stat_user_tables CSV.

Reads a CSV with the columns relname, n_live_tup, n_dead_tup and
last_vacuum, then flags tables whose dead-tuple ratio is above a
threshold. Read-only: it reads the CSV, never the database.

Produce the CSV with:
    psql -d shop -c "COPY (SELECT relname, n_live_tup, n_dead_tup,
        GREATEST(last_vacuum, last_autovacuum) AS last_vacuum
        FROM pg_stat_user_tables) TO STDOUT CSV HEADER" > stats.csv
    python3 bloat_report.py stats.csv
    python3 bloat_report.py - < stats.csv
    python3 bloat_report.py stats.csv --threshold 0.3 --min-dead 500

The ratio is n_dead_tup / (n_live_tup + n_dead_tup). Tables with no
tuples are counted but skipped, and --min-dead keeps tiny tables out of
the report. Flagged tables are printed worst first.

Exit codes:
    0  no table is over the threshold
    1  at least one table is over the threshold
    2  usage error, or a CSV that is missing, has no header, lacks a
       required column, or contains a value that is not an integer

Cron: 15 6 * * * python3 bloat_report.py /var/lib/reports/stats.csv
CI:   python3 bloat_report.py stats.csv --threshold 0.2

By s0sta.com
"""

import argparse
import csv
import io
import sys

FIELDS = ("relname", "n_live_tup", "n_dead_tup", "last_vacuum")


class InputError(Exception):
    """The CSV cannot be used as a stats report."""


def as_int(value, field, row):
    """Parse a non-negative integer from one CSV cell."""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise InputError("row %d: %s is not an integer" % (row, field))
    if number < 0:
        raise InputError("row %d: %s is negative" % (row, field))
    return number


def read_rows(path):
    """Yield normalised rows from a CSV path, or '-' for stdin."""
    handle = None
    try:
        if path == "-":
            text = sys.stdin.read()
            if text.startswith("\ufeff"):
                text = text[1:]
            reader = csv.DictReader(io.StringIO(text), strict=True)
        else:
            handle = open(path, "r", encoding="utf-8-sig", newline="")
            reader = csv.DictReader(handle, strict=True)

        if not reader.fieldnames:
            raise InputError("CSV has no header")
        missing = [field for field in FIELDS if field not in reader.fieldnames]
        if missing:
            raise InputError("CSV is missing columns: %s" % ", ".join(missing))

        rows = []
        for line, raw in enumerate(reader, 2):
            name = (raw.get("relname") or "").strip()
            if not name:
                raise InputError("row %d: relname is empty" % line)
            live = as_int(raw.get("n_live_tup"), "n_live_tup", line)
            dead = as_int(raw.get("n_dead_tup"), "n_dead_tup", line)
            vacuum = (raw.get("last_vacuum") or "").strip() or "never"
            rows.append({"relname": name, "live": live, "dead": dead,
                         "last_vacuum": vacuum})
        return rows
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError("cannot read %s: %s" % (path, exc))
    finally:
        if handle is not None:
            handle.close()


def report(rows, threshold, min_dead):
    """Return (considered, flagged) where flagged is sorted worst first."""
    considered = 0
    flagged = []
    for row in rows:
        considered += 1
        total = row["live"] + row["dead"]
        if total == 0:
            continue
        ratio = row["dead"] / total
        if ratio > threshold and row["dead"] >= min_dead:
            flagged.append({"relname": row["relname"], "live": row["live"],
                            "dead": row["dead"], "ratio": ratio,
                            "last_vacuum": row["last_vacuum"]})
    flagged.sort(key=lambda item: (-item["ratio"], -item["dead"]))
    return considered, flagged


def plural(count, word):
    """Return a count and a correctly pluralised noun."""
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Flag PostgreSQL tables with a high dead-tuple ratio.",
        epilog="Exit 0 clean, 1 finding, 2 usage or input error. By s0sta.com")
    parser.add_argument("csv", help="CSV path, or - for stdin")
    parser.add_argument("--threshold", type=float, default=0.20, metavar="R",
                        help="dead-tuple ratio to flag, between 0 and 1 (default: 0.20)")
    parser.add_argument("--min-dead", type=int, default=1000, metavar="N",
                        help="minimum dead tuples to flag (default: 1000)")
    args = parser.parse_args(argv)

    if not 0 < args.threshold < 1:
        parser.error("--threshold must be greater than 0 and less than 1")
    if args.min_dead < 0:
        parser.error("--min-dead must be zero or positive")

    try:
        rows = read_rows(args.csv)
    except InputError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2

    considered, flagged = report(rows, args.threshold, args.min_dead)
    for item in flagged:
        print("BLOAT %s dead=%d live=%d ratio=%.1f%% last_vacuum=%s"
              % (item["relname"], item["dead"], item["live"],
                 item["ratio"] * 100.0, item["last_vacuum"]))

    if flagged:
        print("FAIL %d of %s over %.1f%% (dead >= %d)"
              % (len(flagged), plural(considered, "table"),
                 args.threshold * 100.0, args.min_dead))
        return 1
    print("OK %s checked, none over %.1f%%"
          % (plural(considered, "table"), args.threshold * 100.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
