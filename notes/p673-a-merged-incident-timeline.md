---
id: p673
title: "A merged incident timeline"
slug: a-merged-incident-timeline
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, IncidentResponse, Observability, SRE, OnCall]
source: "LinkedIn post P673 · IR series"
linkedin_date: 2031-01-14
design: code
script: incident_timeline.py
---

# A merged incident timeline

The incident channel has forty messages and no order. The deploy note is in one thread, the first 500 is in another, and the on-call's timeline starts eight minutes after the alert.

## Quick reference

The full script is at the end of this note: `incident_timeline.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 incident_timeline.py /tmp/s15/tl/*.json --gap-min 5
```

**Example output**

```text
TIMELINE 9 events, 03:01:30 -> 03:38:00
GAP 22 min, 03:14:00 -> 03:36:00, 1 undated
```

## Explained

### What it does

`incident_timeline.py` reads any number of JSON or text sources, takes the timestamp from every event, converts each to UTC, and sorts the dated ones into one timeline. It reports gaps longer than `--gap-min` and lists every event whose timestamp is missing, because an undated event cannot be placed.

### What the screen shows

The panel loads four sources, sorts the nine dated events, finds the longest gap, and prints TIMELINE 9 events, 03:01:30 -> 03:38:00, then GAP 22 min, 03:14:00 -> 03:36:00, 1 undated.

### How to run it

`python3 incident_timeline.py /tmp/s15/tl/*.json --gap-min 5`. Point it at exported alerts, deploy records, chat and logs. Exit 0 is a clean timeline, 1 is a gap or an undated event, 2 is bad input.

### The fix

Write the timestamp at the source, in UTC, before storage. Then merge. The twenty-two minute gap is not empty: it is where the rollback happened, or where nobody looked. Fill it from the deploy log, not from memory.

### Prevention

Make a timestamp mandatory in every exporter, and merge the four clocks on a schedule. A missing timestamp is a data bug, not a formatting preference.

> **The honest caveat:** text logs with stack traces produce many undated lines. Treat each one as a lead, not as noise.

> **The lesson:** an incident without one clock has no sequence, and no sequence means no cause.

## In one line

> **A gap is a finding.** An undated event cannot be placed in the sequence.

**Open one timeline**

```bash
python3 incident_timeline.py *.json
```

## Script: incident_timeline.py

Download: [scripts/incident_timeline.py](../scripts/incident_timeline.py)

```python
#!/usr/bin/env python3
"""incident_timeline.py - merge timestamped events from any sources into one clock.

Every incident has four clocks: the alerting system, the deploy system, the
chat channel and the application log. The postmortem needs one. This script
reads all four, sorts them into a single UTC timeline, and flags the places
where the record goes quiet.

Each source is a JSON file (a list, or an object with an "events" list) or a
plain text file. A JSON event is an object with a timestamp and a message:

    {"ts": "2026-10-20T03:02:10Z", "msg": "API 5xx rate 12%"}

Accepted timestamp keys are ts, timestamp, time and at. Accepted message keys
are msg, message, event and text. An event may carry "source", otherwise the
file name is used. An empty timestamp makes the event undated and it is
reported separately, because it cannot be placed in the timeline.

A text line starts with an ISO timestamp:

    2026-10-20T03:12:30Z ERROR upstream timeout

A non-empty line without that prefix is undated. Blank lines and lines
starting with # are ignored.

Usage:
    python3 incident_timeline.py alerts.json deploys.json chat.json app.log
    python3 incident_timeline.py /var/lib/s0sta/timeline/*.json --gap-min 5
    python3 incident_timeline.py --help

Cron or CI (export the incident sources, then merge them every five minutes):
    */5 * * * * python3 /opt/s0sta/incident_timeline.py /var/lib/s0sta/incident/*.json

Exit codes: 0 no gap over --gap-min and no undated event, 1 at least one gap
or undated event, 2 usage error or unreadable, empty, malformed or untimed
input.

Read-only: opens the given files, parses them and prints. It writes nothing,
changes nothing and makes no network call.

By s0sta.com
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

ISO = re.compile(
    r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?)\s+(.+)$")
TIME_KEYS = ("ts", "timestamp", "time", "at")
MESSAGE_KEYS = ("msg", "message", "event", "text")
DEFAULT_GAP_MIN = 5


class InputError(Exception):
    """An input that cannot be read as timeline data."""


def parse_stamp(value, where):
    """Return an aware UTC datetime, or raise InputError."""
    if not isinstance(value, str) or not value.strip():
        raise InputError("%s: timestamp must be a non-empty ISO string" % where)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        raise InputError("%s: bad timestamp %r" % (where, value))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def first_key(record, keys):
    """Return the first present key from record, or None."""
    for key in keys:
        if key in record:
            return record[key]
    return None


def source_label(path):
    """Return the file stem used when an event has no source field."""
    stem = os.path.splitext(os.path.basename(path))[0]
    for prefix in ("timeline_", "tl_"):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
    return stem or "source"


def load_json(path, text):
    """Return events from a JSON source, or raise InputError."""
    try:
        doc = json.loads(text)
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))
    if isinstance(doc, dict):
        if "events" in doc:
            doc = doc["events"]
        elif "items" in doc:
            doc = doc["items"]
        else:
            raise InputError("%s: object needs an \"events\" list" % path)
    if not isinstance(doc, list):
        raise InputError("%s: expected a list of events" % path)
    label = source_label(path)
    events, undated = [], []
    for index, raw in enumerate(doc, start=1):
        where = "%s event %d" % (path, index)
        if not isinstance(raw, dict):
            raise InputError("%s: expected an object" % where)
        message = first_key(raw, MESSAGE_KEYS)
        if not isinstance(message, str) or not message.strip():
            raise InputError("%s: missing message" % where)
        source = raw.get("source") or label
        if not isinstance(source, str) or not source.strip():
            raise InputError("%s: source must be a string" % where)
        stamp_value = first_key(raw, TIME_KEYS)
        if stamp_value is None or (isinstance(stamp_value, str)
                                   and not stamp_value.strip()):
            undated.append((source.strip(), message.strip()))
            continue
        events.append({
            "stamp": parse_stamp(stamp_value, where),
            "source": source.strip(),
            "message": message.strip(),
        })
    return events, undated


def load_text(path, text):
    """Return events from a text source, or raise InputError."""
    label = source_label(path)
    events, undated = [], []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = ISO.match(line)
        if not match:
            undated.append((label, line))
            continue
        stamp, message = match.groups()
        events.append({
            "stamp": parse_stamp(stamp, "%s line %d" % (path, number)),
            "source": label,
            "message": message.strip(),
        })
    return events, undated


def load_source(path):
    """Return (events, undated) for one source, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    if not text.strip():
        raise InputError("%s: empty input" % path)
    if path.lower().endswith(".json"):
        return load_json(path, text)
    return load_text(path, text)


def merge(paths):
    """Return sorted events and undated items from every source."""
    events, undated = [], []
    for path in paths:
        found, missing = load_source(path)
        events.extend(found)
        undated.extend(missing)
    if not events:
        raise InputError("no timestamped events in %d source(s)" % len(paths))
    events.sort(key=lambda event: (event["stamp"], event["source"],
                                   event["message"]))
    return events, undated


def duration(seconds):
    """Return a compact duration for the gap line."""
    if seconds >= 3600:
        return "%dh%02dm" % (seconds // 3600, (seconds % 3600) // 60)
    if seconds >= 60:
        return "%d min" % (seconds // 60)
    return "%d s" % seconds


def report(events, undated, gap_min):
    """Return (finding, lines) for the merged timeline."""
    first, last = events[0]["stamp"], events[-1]["stamp"]
    if first.date() == last.date():
        span = "%s -> %s" % (first.strftime("%H:%M:%S"),
                             last.strftime("%H:%M:%S"))
    else:
        span = "%s -> %s" % (first.strftime("%Y-%m-%d %H:%M"),
                             last.strftime("%Y-%m-%d %H:%M"))
    lines = ["TIMELINE %d event%s, %s"
             % (len(events), "" if len(events) == 1 else "s", span)]
    for event in events:
        lines.append("%s  %-10s %s"
                     % (event["stamp"].strftime("%H:%M:%S"),
                        event["source"], event["message"]))
    gaps = 0
    for before, after in zip(events, events[1:]):
        seconds = int((after["stamp"] - before["stamp"]).total_seconds())
        if seconds > gap_min * 60:
            gaps += 1
            lines.append("GAP %s, %s -> %s"
                         % (duration(seconds),
                            before["stamp"].strftime("%H:%M"),
                            after["stamp"].strftime("%H:%M")))
    for source, message in undated:
        lines.append("UNDATED %-10s %s" % (source, message))
    if gaps or undated:
        lines.append("FINDING %d gap%s over %d min, %d undated event%s"
                     % (gaps, "" if gaps == 1 else "s", gap_min,
                        len(undated), "" if len(undated) == 1 else "s"))
    else:
        lines.append("OK no gap over %d min, 0 undated" % gap_min)
    return bool(gaps or undated), lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge timestamped incident events into one timeline (read-only).")
    parser.add_argument(
        "sources", nargs="+", metavar="SOURCE",
        help="JSON or text files with timestamped events")
    parser.add_argument(
        "--gap-min", type=int, default=DEFAULT_GAP_MIN, metavar="MIN",
        help="flag a gap longer than this many minutes (default: %d)"
             % DEFAULT_GAP_MIN)
    args = parser.parse_args(argv)

    if args.gap_min < 0:
        parser.error("--gap-min must not be negative")

    try:
        events, undated = merge(args.sources)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    finding, lines = report(events, undated, args.gap_min)
    for line in lines:
        print(line)
    return 1 if finding else 0


if __name__ == "__main__":
    sys.exit(main())
```
