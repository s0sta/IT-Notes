#!/usr/bin/env python3
"""Find root causes that keep coming back, and the services they revisit.

Reads an incident history and groups incidents that share a root-cause tag and
fall inside the same window. A tag that appears twice within --window days is
a recurrence, not bad luck. The report ranks causes by how often they return
and names the services that carry the repeats.

The history is JSON, one object per incident:

    [{"id": "INC-1042", "opened_at": "2026-07-02",
      "root_cause_tags": ["db_pool_exhausted"], "service": "checkout"},
     {"id": "INC-1088", "opened_at": "2026-08-19",
      "root_cause_tags": ["db_pool_exhausted"], "service": "orders"}]

Tags are compared case-insensitively and spaces are collapsed. A window
starts at the first incident in a group and stays open for --window days
(default 90); the next incident after that starts a new window. Two incidents
in the same window make a repeat. The same tag can recur in several windows,
and the report adds them together.

Usage:
    python3 incident_recurrence.py incidents.json
    python3 incident_recurrence.py incidents.json --window 30

Exit codes: 0 no repeated cause, 1 at least one recurrence, 2 usage, or a
history that is missing, unreadable, invalid or empty.

CI (monthly, fail the review when a cause repeats):
    python3 incident_recurrence.py incidents.json --window 90 || exit 1

Cron (first Monday of the month, 08:00, mail the review owner):
    0 8 1-7 * 1 python3 /opt/s0sta/incident_recurrence.py /var/lib/s0sta/incidents.json

The script is read-only. It reads the export and prints the ranking; it does
not merge, close or reopen an incident. A repeat is evidence that the fix did
not hold, not proof of the cause: read the postmortems before you merge them.

Standard library only, Python 3.8+.

By s0sta.com
"""
import argparse
import datetime
import json
import sys


class InputError(Exception):
    """Anything that should end the run with exit code 2."""


def load_incidents(path):
    """Return a non-empty list of incidents, or raise InputError."""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise InputError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(doc, list) or not doc:
        raise InputError("%s has no non-empty incident list" % path)
    return doc


def tags_of(item, incident_id):
    """Return normalised, de-duplicated tags for one incident."""
    raw = item.get("root_cause_tags")
    if not isinstance(raw, list) or not raw:
        raise InputError("incident %s has no root_cause_tags" % incident_id)
    tags = []
    for tag in raw:
        if not isinstance(tag, str) or not tag.strip():
            raise InputError("incident %s has an empty root_cause_tag"
                             % incident_id)
        clean = " ".join(tag.lower().split())
        if clean not in tags:
            tags.append(clean)
    return tags


def incident_fields(item, number):
    """Validate one incident and return (id, date, tags, service)."""
    if not isinstance(item, dict):
        raise InputError("incident %d is not an object" % number)
    incident_id = item.get("id")
    opened_at = item.get("opened_at")
    service = item.get("service")
    if not isinstance(incident_id, str) or not incident_id:
        raise InputError("incident %d has no id" % number)
    if not isinstance(opened_at, str) or len(opened_at) < 10:
        raise InputError("incident %s has no opened_at date" % incident_id)
    try:
        when = datetime.date.fromisoformat(opened_at[:10])
    except ValueError:
        raise InputError("incident %s has an unreadable opened_at: %s"
                         % (incident_id, opened_at))
    if not isinstance(service, str) or not service:
        raise InputError("incident %s has no service" % incident_id)
    return incident_id, when, tags_of(item, incident_id), service


def clusters(events, window):
    """Group (date, incident) pairs into anchored windows."""
    groups = []
    current = []
    start = None
    for when, incident in events:
        if start is None or (when - start).days <= window:
            current.append((when, incident))
            if start is None:
                start = when
        else:
            groups.append(current)
            current = [(when, incident)]
            start = when
    if current:
        groups.append(current)
    return groups


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank root causes that repeat inside a window and flag "
                    "the services that keep meeting them.",
        epilog="Exit codes: 0 no recurrence, 1 recurrence found, "
               "2 usage or input error.")
    parser.add_argument("incidents", help="JSON list of incidents")
    parser.add_argument("--window", type=int, default=90,
                        help="window in days (default: 90)")
    args = parser.parse_args(argv)

    if args.window < 1:
        print("ERR --window must be at least 1 day", file=sys.stderr)
        return 2

    try:
        events = load_incidents(args.incidents)
        seen = set()
        by_tag = {}
        services = {}
        for number, item in enumerate(events, 1):
            incident_id, when, tags, service = incident_fields(item, number)
            if incident_id in seen:
                raise InputError("duplicate incident id %s" % incident_id)
            seen.add(incident_id)
            services[incident_id] = service
            for tag in tags:
                by_tag.setdefault(tag, []).append((when, incident_id))
    except InputError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2

    causes = {}
    for tag, entries in by_tag.items():
        entries.sort()
        for group in clusters(entries, args.window):
            if len(group) < 2:
                continue
            count, repeats = causes.get(tag, (0, 0))
            causes[tag] = (count + len(group), repeats + len(group) - 1)

    ranked = sorted(causes.items(), key=lambda kv: (-kv[1][1], -kv[1][0], kv[0]))
    if ranked:
        print("FINDING %d recurring causes" % len(ranked))
        for tag, (count, _) in ranked:
            print("REPEAT %s %d incidents" % (tag, count))

        # A service is flagged when it appears in at least two incidents that
        # sit inside a recurring window. A set per service prevents
        # double-counting an incident that carries two recurring tags.
        hits = {}
        for tag, entries in by_tag.items():
            for group in clusters(sorted(entries), args.window):
                if len(group) < 2:
                    continue
                for _, incident_id in group:
                    hits.setdefault(services[incident_id], set()).add(incident_id)
        flagged = sorted((len(ids), name) for name, ids in hits.items()
                         if len(ids) >= 2)
        for count, name in sorted(flagged, key=lambda x: (-x[0], x[1])):
            print("SERVICE %s %d repeat incidents" % (name, count))
        return 1
    print("OK no root cause repeated inside %d days" % args.window)
    return 0


if __name__ == "__main__":
    sys.exit(main())
