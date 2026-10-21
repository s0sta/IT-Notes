#!/usr/bin/env python3
"""action_items.py - measure the action items a postmortem promised.

Reads a postmortem action list and reports the three reasons an item never
closes: it is past its due date, it has no owner, or it duplicates another
item. The overdue rate is the number of overdue open items divided by the
number of open items; when that rate passes --max-overdue the tool exits 1,
so a tracker that is quietly rotting fails the build like any other check.

The items file is a JSON list. Only "id" is required:

    [{"id": "A-1", "owner": "payments", "due": "2026-10-24",
      "status": "open", "duplicate_of": null},
     {"id": "A-2", "owner": "", "due": "2026-10-01", "status": "open"},
     {"id": "A-3", "owner": "sre", "due": "2026-10-12",
      "status": "open", "duplicate_of": "A-2"}]

Usage:
    python3 action_items.py items.json
    python3 action_items.py items.json --now 2026-10-21 --max-overdue 10
    python3 action_items.py items.json --strict
    python3 action_items.py --help

CI (fail the week the action list stops closing):
    python3 action_items.py postmortem/actions.json --now "$(date -u +%F)" || exit 1

Cron (Monday morning report, mailed by the CI job):
    0 7 * * 1 python3 /opt/s0sta/action_items.py /srv/postmortems/actions.json --now "$(date -u +%F)"

Exit codes: 0 the overdue rate is at or below --max-overdue, 1 it is above,
2 usage error or unreadable JSON. With --strict, 1 also covers any open item
without an owner and any duplicate that is still open.

Read-only: opens the items file, prints, and writes nothing. A "due" date is
read as the end of that day in UTC, so an item due today is not overdue yet.

By s0sta.com
"""
import argparse
import datetime
import json
import sys

CLOSED = {"done", "closed", "dropped", "cancelled", "wontfix", "won't fix"}


class InputError(Exception):
    """An input that cannot be measured."""


def parse_day(raw):
    """Return a UTC datetime for an ISO date or datetime, or raise InputError."""
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except ValueError:
        raise InputError("%s: not an ISO date" % raw)
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    if len(text) <= 10:
        stamp = stamp.replace(hour=23, minute=59, second=59)
    return stamp


def load_items(path, now):
    """Return a list of normalised item dicts, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s: not JSON (%s)" % (path, exc))
    if isinstance(data, dict):
        data = data.get("items")
    if not isinstance(data, list) or not data:
        raise InputError("%s: expected a non-empty list of items" % path)

    items = []
    for index, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            raise InputError("%s: item %d is not an object" % (path, index))
        item = {key: str(value).strip() for key, value in row.items()
                if not isinstance(value, (dict, list)) and value is not None}
        if not item.get("id"):
            raise InputError("%s: item %d has no id" % (path, index))
        status = item.get("status", "open").lower()
        item["open"] = status not in CLOSED
        item["overdue"] = False
        if item["open"] and item.get("due"):
            item["overdue"] = parse_day(item["due"]) < now
        items.append(item)
    return items


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report the action items a postmortem never closed (read-only).")
    parser.add_argument("items", help="action items JSON file")
    parser.add_argument("--now", metavar="DATE",
                        help="treat this date as today (default: the clock in UTC)")
    parser.add_argument("--max-overdue", type=float, default=20.0, metavar="PCT",
                        help="fail when the overdue rate is above this percentage (default 20)")
    parser.add_argument("--strict", action="store_true",
                        help="also fail on an unowned open item or an open duplicate")
    args = parser.parse_args(argv)

    if args.max_overdue < 0 or args.max_overdue > 100:
        print("ERROR --max-overdue must be between 0 and 100", file=sys.stderr)
        return 2

    try:
        now = parse_day(args.now) if args.now else datetime.datetime.utcnow().replace(
            microsecond=0)
        if args.now and len(str(args.now).strip()) <= 10:
            now = now.replace(hour=12, minute=0, second=0)
        items = load_items(args.items, now)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    open_items = [item for item in items if item["open"]]
    overdue = [item for item in open_items if item["overdue"]]
    unowned = [item for item in open_items if not item.get("owner")]
    duplicates = [item for item in items if item.get("duplicate_of")]
    rate = (100.0 * len(overdue) / len(open_items)) if open_items else 0.0

    print("ACTIONS %d items, %d open, %d overdue, %d unowned"
          % (len(items), len(open_items), len(overdue), len(unowned)))
    for item in overdue:
        print("OVERDUE %s due %s" % (item["id"], item.get("due", "-")))
    for item in unowned:
        print("UNOWNED %s" % item["id"])
    for item in duplicates:
        print("DUPLICATE %s -> %s" % (item["id"], item["duplicate_of"]))
    print("RATE %.0f%% overdue of %d open, limit %.0f%%"
          % (rate, len(open_items), args.max_overdue))

    if rate > args.max_overdue:
        return 1
    if args.strict and (unowned or any(item["open"] for item in duplicates)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
