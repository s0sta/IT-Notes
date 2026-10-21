---
id: p703
title: "A status page draft"
slug: a-status-page-draft
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, IncidentResponse, SRE, StatusPage, CyberSecurity]
source: "LinkedIn post P703 · IR series"
linkedin_date: 2031-03-25
design: code
script: status_update.py
---

# A status page draft

At 03:40 the incident channel has two hundred messages and the status page still carries the 03:10 entry: we are investigating. Nobody has written the next one.

## Quick reference

The full script is at the end of this note: `status_update.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 status_update.py status/partial.json identified
```

**Example output**

```text
STATUS identified INC-214 Checkout errors
MISSING next_update
```

## Explained

### What it does

`status_update.py` reads the incident JSON and the phase, then prints the fields a status page needs: what happened, the impact, the action, the owner and the next update time. Each phase has its own required set. Investigating may say the impact is still being measured; identified and later must state it, so unknown and assessing are rejected as placeholders. A missing field is printed as MISSING and the exit code is 1.

### What the screen shows

The thirteen lines load the incident, hold the phase table, collect the missing fields and print STATUS identified INC-214 Checkout errors, then MISSING next_update.

### How to run it

`python3 status_update.py incident.json` monitoring `--at 2026-10-20T03:16:00Z`. Exit 0 is a complete draft, 1 a missing field, 2 an unknown phase or unreadable JSON. In cron, draft the update five minutes before it is due.

### The fix

The draft is the checklist. If the next update time is missing, you do not have an update, you have a sentence. Publish the time, then keep it.

### Prevention

Put the required fields in the template, not in the reviewer's memory, and let the phase decide which are mandatory.

> **The honest caveat:** the tool can check that an impact figure exists, not that it is true.

> **The lesson:** a status page is a promise with a timestamp.

## In one line

> **An update without a next time is a rumour.** The page needs a time it will be true again, not just a mood.

**Draft the update**

```bash
python3 status_update.py inc.json identified
```

## Script: status_update.py

Download: [scripts/status_update.py](../scripts/status_update.py)

```python
#!/usr/bin/env python3
"""status_update.py - draft the status page update from an incident file.

Reads an incident JSON and a phase (investigating, identified, monitoring or
resolved), then prints the update a status page needs: what happened, the
impact, the action, the owner and the next update time. Every field the
phase requires is checked, and a missing impact or next-update time is
printed as MISSING, which is the difference between an update and a
sentence.

The incident file is a JSON object. Only id and title are required:

    {"id": "INC-214", "title": "Checkout errors",
     "impact": "4.1% of card payments failing since 03:04Z",
     "action": "Roll back release 2026.10.20-3 and replay the queue",
     "owner": "payments on-call",
     "next_update": "2026-10-20T03:34:00Z"}

Usage:
    python3 status_update.py incident.json investigating
    python3 status_update.py incident.json identified --at 2026-10-20T03:16:00Z
    python3 status_update.py incident.json resolved
    python3 status_update.py --help

CI (refuse to publish an update that names no impact and no next time):
    python3 status_update.py incident.json monitoring --at "$(date -u +%FT%TZ)" || exit 1

Cron (draft the next update before the promised time):
    */5 * * * * python3 /opt/s0sta/status_update.py /cases/inc-214.json monitoring > /tmp/update.txt

Exit codes: 0 the draft is complete, 1 a required field is missing or holds
a placeholder, 2 usage error, unreadable JSON or an unknown phase.

Read-only: opens the incident file, prints, and writes nothing.

The phase is not decoration. Investigating needs the impact and a next update
time, and accepts a placeholder while the impact is being measured, because
a number at 03:12 would be a guess. Identified and later also need the action,
and a placeholder impact is rejected there. Every phase needs a next update
time, because a page that will never speak again is a page nobody follows.

By s0sta.com
"""
import argparse
import datetime
import json
import sys

PHASES = ("investigating", "identified", "monitoring", "resolved")
REQUIRED = {
    "investigating": ("impact", "next_update"),
    "identified": ("impact", "action", "next_update"),
    "monitoring": ("impact", "action", "next_update"),
    "resolved": ("impact", "action", "next_update"),
}
PLACEHOLDERS = {"unknown", "tbd", "tba", "n/a", "na", "none", "-", "?", "assessing", ""}


class InputError(Exception):
    """An input that cannot be used."""


def parse_at(raw):
    """Return an aware UTC datetime from ISO 8601 text, or raise InputError."""
    text = raw.strip().replace("Z", "+00:00").replace("z", "+00:00")
    try:
        stamp = datetime.datetime.fromisoformat(text)
    except ValueError:
        raise InputError("%s: not an ISO 8601 time" % raw)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    return stamp.astimezone(datetime.timezone.utc)


def load_json(path):
    """Return the parsed JSON, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s: not JSON (%s)" % (path, exc))
    return data


def normalise(data):
    """Return the incident as a dict of strings, or raise InputError."""
    if not isinstance(data, dict):
        raise InputError("incident: expected a JSON object")
    incident = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            continue
        incident[str(key)] = str(value).strip()
    for key in ("id", "title"):
        if not incident.get(key):
            raise InputError("incident: %s is required" % key)
    return incident


def relative(stamp, at):
    """Return a short description of a time relative to --at."""
    minutes = int(round((stamp - at).total_seconds() / 60.0))
    if minutes == 0:
        return "now"
    if minutes > 0:
        return "in %d min" % minutes
    return "%d min late" % -minutes


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Draft a status page update from an incident file (read-only).")
    parser.add_argument("incident", help="incident JSON file")
    parser.add_argument("phase", help="one of: " + ", ".join(PHASES))
    parser.add_argument("--at", metavar="ISO",
                        help="treat this time as now (default: the clock in UTC)")
    args = parser.parse_args(argv)

    if args.phase not in PHASES:
        print("ERROR unknown phase %r, expected one of: %s"
              % (args.phase, ", ".join(PHASES)), file=sys.stderr)
        return 2

    try:
        incident = normalise(load_json(args.incident))
        at = parse_at(args.at) if args.at else datetime.datetime.now(datetime.timezone.utc)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    required = REQUIRED[args.phase]
    missing = []
    print("STATUS %s %s %s" % (args.phase, incident["id"], incident["title"]))
    for field in ("impact", "action", "owner"):
        value = incident.get(field, "")
        if field not in required:
            if value:
                print("%s %s" % (field.upper(), value))
            continue
        if not value:
            missing.append(field)
            continue
        if field == "impact" and args.phase != "investigating" and value.lower() in PLACEHOLDERS:
            missing.append(field)
            continue
        print("%s %s" % (field.upper(), value))

    if "next_update" in required:
        raw = incident.get("next_update", "")
        if not raw:
            missing.append("next_update")
        else:
            try:
                stamp = parse_at(raw)
                print("NEXT UPDATE %s (%s)" % (raw, relative(stamp, at)))
            except InputError:
                missing.append("next_update")
    elif incident.get("next_update"):
        print("NEXT UPDATE %s" % incident["next_update"])
    for field in missing:
        print("MISSING %s" % field)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
```
