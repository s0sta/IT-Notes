#!/usr/bin/env python3
"""timeline_export.py - export incident events as a markdown timeline.

Reads an events JSON file and writes a markdown table with the time, the
event, the actor, the source and the evidence reference for each row. It
sorts the rows by time, keeps events that carry no timestamp in their own
section at the end, and flags every event with no timestamp or no source,
because an unsourced row is a memory, not evidence.

The events file is a JSON list. Only "event" is required:

    [{"at": "2026-10-20T03:04:00Z", "event": "Checkout error rate 4.1%",
      "actor": "alertmanager", "source": "mon-prod", "evidence": "ev-001"},
     {"at": "2026-10-20T03:19:00Z", "event": "Deploy 2026.10.20-3 finished",
      "actor": "cd", "source": "cd-prod", "evidence": "ev-004"}]

Usage:
    python3 timeline_export.py events.json
    python3 timeline_export.py events.json --out timeline.md
    python3 timeline_export.py events.json --title "INC-214 checkout errors"
    python3 timeline_export.py --help

CI (refuse to publish a timeline with an unsourced event):
    python3 timeline_export.py events.json --out timeline.md || exit 1

Cron (refresh the public timeline every five minutes):
    */5 * * * * python3 /opt/s0sta/timeline_export.py /cases/inc-214/events.json --out /srv/status/timeline.md

Exit codes: 0 every event has a timestamp and a source, 1 at least one event
is missing a timestamp or a source, 2 usage error or unreadable JSON.

Read-only: reads the events file and prints or writes the markdown file named
by --out, and nothing else.

The table is the export, not the record. Keep the JSON beside it and hash
both; a markdown table that was edited after the incident is a story, not a
timeline.

By s0sta.com
"""
import argparse
import datetime
import json
import sys

COLUMNS = ("Time", "Event", "Actor", "Source", "Evidence")


class InputError(Exception):
    """An input that cannot be exported."""


def parse_at(raw):
    """Return a naive UTC datetime from loose ISO text, or None."""
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00").replace("z", "+00:00")
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return stamp


def load_events(path):
    """Return a list of event dicts, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s: not JSON (%s)" % (path, exc))
    if isinstance(data, dict):
        data = data.get("events")
    if not isinstance(data, list):
        raise InputError("%s: expected a list of events" % path)
    events = []
    for index, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            raise InputError("%s: event %d is not an object" % (path, index))
        event = {key: str(value).strip() for key, value in row.items()
                 if not isinstance(value, (dict, list)) and value is not None}
        event["event"] = event.get("event", "").strip()
        if not event["event"]:
            raise InputError("%s: event %d has no event text" % (path, index))
        events.append(event)
    if not events:
        raise InputError("%s: no events" % path)
    return events


def cell(value):
    """Return a markdown table cell, escaping pipes and collapsing newlines."""
    text = " ".join(str(value or "").split())
    return text.replace("|", "\\|") if text else "-"


def sort_key(event):
    stamp = parse_at(event.get("at", ""))
    return (stamp is None, stamp or datetime.datetime.max)


def build(events, title):
    """Return (lines, flags) for the timeline."""
    flags = []
    no_time, no_source = 0, 0
    dated, undated = [], []
    for event in events:
        if parse_at(event.get("at", "")):
            dated.append(event)
        else:
            undated.append(event)
            no_time += 1
            flags.append((event["event"], "TIMESTAMP"))
        if not event.get("source"):
            no_source += 1
            flags.append((event["event"], "SOURCE"))
    dated.sort(key=sort_key)
    stamps = [parse_at(event.get("at", "")) for event in dated]
    days = sorted({stamp.date() for stamp in stamps})
    multi = len(days) > 1

    heading = "# Timeline - %s" % title
    if len(days) == 1:
        heading += " (%s)" % days[0].isoformat()
    lines = [heading, ""]
    lines.append("| " + " | ".join(COLUMNS) + " |")
    lines.append("| " + " | ".join("---" for _ in COLUMNS) + " |")
    for stamp, event in zip(stamps, dated):
        shown = stamp.strftime("%m-%d %H:%MZ" if multi else "%H:%MZ")
        lines.append("| %s | %s | %s | %s | %s |" % (
            cell(shown), cell(event["event"]), cell(event.get("actor")),
            cell(event.get("source")), cell(event.get("evidence"))))
    if undated:
        lines.extend(["", "## No timestamp", ""])
        for event in undated:
            lines.append("- %s%s" % (
                cell(event["event"]),
                " (actor %s)" % cell(event["actor"]) if event.get("actor") else ""))
    if flags:
        lines.extend(["", "## Flags", ""])
        for text, reason in flags:
            lines.append("NO %s %s" % (reason, text))
    if flags:
        lines.append("")
        lines.append("FLAGS %d, no timestamp %d, no source %d"
                     % (len(flags), no_time, no_source))
    return lines, flags


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Export incident events as a markdown timeline (read-only).")
    parser.add_argument("events", help="events JSON file")
    parser.add_argument("--out", metavar="FILE", help="write the markdown here instead of stdout")
    parser.add_argument("--title", default="", help="incident title for the heading")
    args = parser.parse_args(argv)

    try:
        events = load_events(args.events)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    title = args.title.strip() or "incident"
    lines, flags = build(events, title)
    body = "\n".join(lines) + "\n"
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(body)
        except OSError as exc:
            print("ERROR %s: %s" % (args.out, exc.strerror or exc), file=sys.stderr)
            return 2
        print("WROTE %s, %d events, %d flags" % (args.out, len(events), len(flags)))
    else:
        sys.stdout.write(body)
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
