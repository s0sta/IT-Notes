#!/usr/bin/env python3
"""handoff_brief.py - build the change-of-shift brief from incidents and the rota.

A handoff is not a channel summary. It is a short, ordered brief that says what
is still open, which pages nobody acknowledged, which actions are still
pending and which risks the next person inherits. This script reads the open
incidents and the on-call rota and prints that brief. It exits 1 when a
critical incident is still unacknowledged, because that is the item a handoff
must never bury.

The incidents file is a JSON list, or an object with an "incidents" list:

    {"id": "INC-1042", "title": "payments API 5xx", "severity": "SEV1",
     "status": "paged", "opened_at": "2026-10-20T02:19:00Z",
     "owner": null, "actions": ["capture heap dump"]}

Status is paged, open, acknowledged, mitigated, resolved or closed. Paged and
open count as unacknowledged; resolved and closed leave the brief. Severity is
SEV1 to SEV4. Critical means SEV1 or SEV2.

The rota file names the primary and, optionally, the secondary and shift end:

    {"primary": "ana", "secondary": "sam", "shift_end": "2026-10-20T07:00:00Z"}

Usage:
    python3 handoff_brief.py incidents.json rota.json
    python3 handoff_brief.py incidents.json rota.json --now 2026-10-20T03:00:00Z
    python3 handoff_brief.py --help

Cron (post the brief to the on-call channel fifteen minutes before the shift):
    45 6,14,22 * * * python3 /opt/s0sta/handoff_brief.py /var/lib/s0sta/incidents.json /etc/s0sta/rota.json

Exit codes: 0 no critical item is unacknowledged, 1 a critical item is
unacknowledged, 2 usage error or unreadable, empty or malformed input.

Read-only: opens the two files, compares them and prints. It writes nothing,
changes nothing and makes no network call.

By s0sta.com
"""
import argparse
import json
import sys
from datetime import datetime, timezone

SEVERITY_RANK = {"SEV1": 0, "SEV2": 1, "SEV3": 2, "SEV4": 3}
UNACKED = ("paged", "open")
OPEN = ("paged", "open", "acknowledged", "mitigated")
CRITICAL = ("SEV1", "SEV2")
DEFAULT_TOP = 3


class InputError(Exception):
    """An input that cannot become a brief."""


def read_json(path):
    """Return a decoded JSON document, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))


def parse_stamp(value, where):
    """Return an aware UTC datetime, or raise InputError."""
    if not isinstance(value, str) or not value.strip():
        raise InputError("%s: expected an ISO timestamp" % where)
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


def load_incidents(path):
    """Return validated incidents, or raise InputError."""
    doc = read_json(path)
    if isinstance(doc, dict):
        if "incidents" not in doc:
            raise InputError("%s: object needs an \"incidents\" list" % path)
        doc = doc["incidents"]
    if not isinstance(doc, list):
        raise InputError("%s: expected a list of incidents" % path)
    if not doc:
        raise InputError("%s: no incidents in input" % path)
    incidents = []
    for index, raw in enumerate(doc, start=1):
        where = "incident %d" % index
        if not isinstance(raw, dict):
            raise InputError("%s: expected an object" % where)
        incident_id = raw.get("id")
        title = raw.get("title")
        severity = raw.get("severity")
        status = raw.get("status")
        owner = raw.get("owner")
        actions = raw.get("actions", [])
        if not isinstance(incident_id, str) or not incident_id.strip():
            raise InputError("%s: missing id" % where)
        if not isinstance(title, str) or not title.strip():
            raise InputError("%s: missing title" % where)
        if severity not in SEVERITY_RANK:
            raise InputError("%s: severity must be SEV1 to SEV4" % where)
        if status not in OPEN + ("resolved", "closed"):
            raise InputError("%s: unknown status %r" % (where, status))
        if owner is not None and (not isinstance(owner, str)
                                  or not owner.strip()):
            raise InputError("%s: owner must be a name or null" % where)
        if not isinstance(actions, list):
            raise InputError("%s: actions must be a list" % where)
        clean_actions = []
        for action in actions:
            if not isinstance(action, str) or not action.strip():
                raise InputError("%s: actions must be non-empty strings" % where)
            clean_actions.append(action.strip())
        incidents.append({
            "id": incident_id.strip(),
            "title": title.strip(),
            "severity": severity,
            "status": status,
            "opened": parse_stamp(raw.get("opened_at"),
                                  "%s opened_at" % where),
            "owner": owner.strip() if isinstance(owner, str) else None,
            "actions": clean_actions,
        })
    return incidents


def load_rota(path):
    """Return a validated rota, or raise InputError."""
    doc = read_json(path)
    if not isinstance(doc, dict):
        raise InputError("%s: expected a JSON object" % path)
    primary = doc.get("primary")
    secondary = doc.get("secondary")
    if not isinstance(primary, str) or not primary.strip():
        raise InputError("%s: missing primary" % path)
    if secondary is not None and (not isinstance(secondary, str)
                                  or not secondary.strip()):
        raise InputError("%s: secondary must be a name or null" % path)
    shift_end = doc.get("shift_end")
    if shift_end is not None:
        shift_end = parse_stamp(shift_end, "%s shift_end" % path)
    return {
        "primary": primary.strip(),
        "secondary": secondary.strip() if isinstance(secondary, str) else None,
        "shift_end": shift_end,
    }


def minutes_between(start, end):
    """Return whole minutes from start to end, or raise InputError."""
    seconds = int((end - start).total_seconds())
    if seconds < 0:
        raise InputError("opened_at is after --now")
    return seconds // 60


def report(incidents, rota, now, top):
    """Return (finding, lines) for the handoff brief."""
    open_items = [item for item in incidents if item["status"] in OPEN]
    open_items.sort(key=lambda item: (SEVERITY_RANK[item["severity"]],
                                     item["opened"], item["id"]))
    unacked = [item for item in open_items if item["status"] in UNACKED]
    critical = [item for item in unacked if item["severity"] in CRITICAL]
    actions = sum(len(item["actions"]) for item in open_items)
    lines = ["HANDOFF %s: %d open, %d unacked, %d action%s"
             % (rota["primary"], len(open_items), len(unacked), actions,
                "" if actions == 1 else "s")]
    if rota["secondary"]:
        if rota["shift_end"]:
            lines.append("ROTA %s -> %s, shift ends %sZ"
                         % (rota["primary"], rota["secondary"],
                            rota["shift_end"].strftime("%H:%M")))
        else:
            lines.append("ROTA %s -> %s" % (rota["primary"],
                                            rota["secondary"]))
    else:
        lines.append("ROTA %s, no secondary" % rota["primary"])
    for item in open_items[:top]:
        lines.append("TOP %s %s %s, %s %d min"
                     % (item["id"], item["severity"], item["title"],
                        item["status"], minutes_between(item["opened"], now)))
    if unacked:
        lines.append("UNACKED " + ", ".join(
            "%s %s" % (item["id"], item["severity"]) for item in unacked))
    else:
        lines.append("UNACKED none")
    if actions:
        parts = ["%s x%d" % (item["id"], len(item["actions"]))
                 for item in open_items if item["actions"]]
        lines.append("ACTIONS %d pending: %s" % (actions, ", ".join(parts)))
    else:
        lines.append("ACTIONS none pending")

    risks = []
    for item in critical:
        risks.append("critical unacknowledged: %s" % item["id"])
    for item in open_items:
        if item["severity"] in CRITICAL and not item["owner"]:
            risks.append("no owner: %s" % item["id"])
    if not rota["secondary"]:
        risks.append("no secondary on the rota")
    if risks:
        for risk in risks:
            lines.append("RISK " + risk)
    else:
        lines.append("RISK none at handoff")

    if critical:
        worst = critical[0]
        lines.append("ALERT %s %s unacked %d min"
                     % (worst["id"], worst["severity"],
                        minutes_between(worst["opened"], now)))
        lines.append("FINDING %d critical item%s unacknowledged"
                     % (len(critical), "" if len(critical) == 1 else "s"))
    else:
        lines.append("OK no critical item unacknowledged")
    return bool(critical), lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the on-call handoff brief (read-only).")
    parser.add_argument("incidents", help="open incidents JSON")
    parser.add_argument("rota", help="on-call rota JSON")
    parser.add_argument(
        "--now", default=None, metavar="ISO",
        help="evaluate ages at this UTC timestamp (default: now)")
    parser.add_argument(
        "--top", type=int, default=DEFAULT_TOP, metavar="N",
        help="show at most N top items (default: %d)" % DEFAULT_TOP)
    args = parser.parse_args(argv)

    if args.top < 1:
        parser.error("--top must be at least 1")

    try:
        incidents = load_incidents(args.incidents)
        rota = load_rota(args.rota)
        now = (parse_stamp(args.now, "--now") if args.now
               else datetime.now(timezone.utc))
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    try:
        finding, lines = report(incidents, rota, now, args.top)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    return 1 if finding else 0


if __name__ == "__main__":
    sys.exit(main())
