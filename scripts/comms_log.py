#!/usr/bin/env python3
"""comms_log.py - who was told, when, and who was missed.

Reads a notification log and a stakeholder list, then reports the two
numbers every incident review asks for: the notification latency (how long
after the start each stakeholder heard) and the gaps between updates. It
names every required stakeholder with no notification at all, and flags the
gap between the start and the first update, which is where most of the
damage is done.

The log is a JSON object:

    {"incident": "INC-214", "started": "2026-10-20T03:04:00Z",
     "notifications": [
       {"to": "cto", "at": "2026-10-20T03:38:00Z", "channel": "phone"},
       {"to": "support", "at": "2026-10-20T03:41:00Z", "channel": "slack"}]}

The stakeholders file is a list of names, or a list of objects with "name"
and an optional "required" flag (default true):

    ["cto", "legal", "support"]
    [{"name": "cto", "team": "exec"}, {"name": "legal", "required": false}]

Usage:
    python3 comms_log.py log.json stakeholders.json
    python3 comms_log.py log.json stakeholders.json --start 2026-10-20T03:04:00Z
    python3 comms_log.py log.json stakeholders.json --target 15
    python3 comms_log.py --help

CI (fail the review when a required stakeholder was never told):
    python3 comms_log.py log.json stakeholders.json --target 15 || exit 1

Cron (draft the comms section of the review every hour):
    7 * * * * python3 /opt/s0sta/comms_log.py /cases/inc-214/log.json /cases/inc-214/stakeholders.json

Exit codes: 0 every required stakeholder was told and no gap is over
--target minutes, 1 someone was missed or a gap is too long, 2 usage error or
unreadable JSON.

Read-only: reads the two files, prints, and writes nothing. The log records
who was told, never what they were told, so the tool cannot leak the content
of a notification.

By s0sta.com
"""
import argparse
import datetime
import json
import sys

DEFAULT_TARGET = 30


class InputError(Exception):
    """An input that cannot be measured."""


def parse_at(raw):
    """Return an aware UTC datetime from ISO text, or raise InputError."""
    text = str(raw).strip().replace("Z", "+00:00").replace("z", "+00:00")
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except ValueError:
        raise InputError("%s: not an ISO 8601 time" % raw)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    return stamp.astimezone(datetime.timezone.utc)


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s: not JSON (%s)" % (path, exc))


def load_log(path):
    """Return (incident name, start, notifications) or raise InputError."""
    data = load_json(path)
    if not isinstance(data, dict):
        raise InputError("%s: expected a JSON object" % path)
    if not data.get("started"):
        raise InputError("%s: started is required" % path)
    started = parse_at(data["started"])
    rows = data.get("notifications")
    if not isinstance(rows, list):
        raise InputError("%s: notifications must be a list" % path)
    notes = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or not row.get("to") or not row.get("at"):
            raise InputError("%s: notification %d needs to and at" % (path, index))
        notes.append({"to": str(row["to"]).strip(), "at": parse_at(row["at"]),
                      "channel": str(row.get("channel", "")).strip(),
                      "update": row.get("update")})
    notes.sort(key=lambda note: note["at"])
    return str(data.get("incident", "incident")), started, notes


def load_stakeholders(path):
    """Return a list of (name, required) or raise InputError."""
    data = load_json(path)
    if isinstance(data, dict):
        data = data.get("stakeholders")
    if not isinstance(data, list) or not data:
        raise InputError("%s: expected a list of stakeholders" % path)
    people = []
    for index, row in enumerate(data, start=1):
        if isinstance(row, str):
            people.append((row.strip(), True))
            continue
        if not isinstance(row, dict) or not row.get("name"):
            raise InputError("%s: stakeholder %d has no name" % (path, index))
        people.append((str(row["name"]).strip(), bool(row.get("required", True))))
    return people


def minutes(delta):
    return int(round(delta.total_seconds() / 60.0))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report notification latency and missed stakeholders (read-only).")
    parser.add_argument("log", help="notification log JSON file")
    parser.add_argument("stakeholders", help="stakeholder list JSON file")
    parser.add_argument("--start", metavar="ISO",
                        help="override the incident start time in the log")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET, metavar="MIN",
                        help="maximum acceptable gap in minutes (default %d)" % DEFAULT_TARGET)
    args = parser.parse_args(argv)

    if args.target <= 0:
        print("ERROR --target must be a positive number of minutes", file=sys.stderr)
        return 2

    try:
        name, started, notes = load_log(args.log)
        if args.start:
            started = parse_at(args.start)
        people = load_stakeholders(args.stakeholders)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    first = {}
    for note in notes:
        first.setdefault(note["to"], note["at"])
    missed = [who for who, required in people if required and who not in first]
    told = sum(1 for who, _ in people if who in first)
    latencies = sorted((minutes(stamp - started), who) for who, stamp in first.items())
    gaps = []
    if notes:
        gaps.append({"min": minutes(notes[0]["at"] - started), "from": started,
                     "to": notes[0]["at"], "start": True})
    for earlier, later in zip(notes, notes[1:]):
        if later["at"] > earlier["at"]:
            gaps.append({"min": minutes(later["at"] - earlier["at"]),
                         "from": earlier["at"], "to": later["at"], "start": False})
    worst = max(gaps, key=lambda gap: gap["min"]) if gaps else {
        "min": 0, "from": started, "to": started, "start": False}

    print("COMMS %d updates to %d of %d stakeholders" % (len(notes), told, len(people)))
    if missed:
        print("MISSED %s" % ", ".join(missed))
    if latencies:
        slow = max(latencies)
        print("LATENCY first %d min, slowest %d min (%s)"
              % (latencies[0][0], slow[0], slow[1]))
    else:
        print("LATENCY none, no stakeholder was told")
    if not gaps:
        print("GAP none, target %d" % args.target)
    else:
        if worst["start"]:
            window = "before the first update"
        else:
            window = "%s to %s" % (worst["from"].strftime("%H:%MZ"),
                                   worst["to"].strftime("%H:%MZ"))
        print("GAP %d min %s, target %d" % (worst["min"], window, args.target))
    print("INCIDENT %s started %s" % (name, started.strftime("%Y-%m-%dT%H:%M:%SZ")))

    if missed or worst["min"] > args.target:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
