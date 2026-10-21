#!/usr/bin/env python3
"""restore_point.py - pick a restorable point before an incident.

Reads a backup catalog and answers one question: which snapshot can I restore
to, and with what command? A candidate must have been taken before the
incident (restoring to a later point restores the damage), inside --window
hours, with a restorable status and a non-zero size. Candidates are ranked
newest first and the newest one wins.

Catalog (metadata only; size is in GiB):

    {"snapshots": [
      {"id": "snap-2210", "taken_at": "2026-10-20T22:00:00Z",
       "status": "completed", "size_gb": 412},
      {"id": "snap-2310", "taken_at": "2026-10-20T23:10:00Z",
       "status": "creating", "size_gb": 0}
    ]}

Restorable status: available, complete, completed, ok or restorable. Anything else is skipped and named, so a creating snapshot cannot
win by being the newest. The script prints the plan and the provider command;
it never calls the provider and never restores anything.

Usage:
    python3 restore_point.py catalog.json --incident 2026-10-20T23:40:00Z
    python3 restore_point.py catalog.json --incident 2026-10-20T23:40:00Z \
        --window 12 --provider gcp
    cat catalog.json | python3 restore_point.py - --incident 2026-10-20T23:40:00Z

Cron (daily, report the restore point for yesterday's incident window):
    0 6 * * * python3 /opt/s0sta/restore_point.py /etc/ir/catalog.json \
      --incident "$(date -u -d yesterday +%FT%TZ)" >> /var/log/ir/restore.log 2>&1

CI (fail when a window has no restorable point):
    python3 restore_point.py catalog.json --incident "$INCIDENT" || exit 1

Exit codes: 0 at least one candidate qualifies, 1 none qualifies, 2 usage
error or unreadable, invalid or empty input.

Read-only: the catalog is opened for reading only. The printed command is a
suggestion for a human; it is never executed. The status field is the backup
system's claim, not a restore test; only a real restore proves the bytes.

By s0sta.com
"""
import argparse
import json
import sys
from datetime import datetime, timezone

RESTORABLE = {"available", "complete", "completed", "ok", "restorable"}
KNOWN_BAD = {"creating", "pending", "in_progress", "running", "recovering",
             "failed", "error", "deleted", "expired", "aborted"}


def die(message):
    print("ERROR " + message, file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        if path == "-":
            return json.load(sys.stdin)
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        die("%s: %s" % (path, exc.strerror or exc))
    except (ValueError, UnicodeError) as exc:
        die("%s: not valid JSON (%s)" % (path, exc))


def rows_of(document):
    rows = document.get("snapshots") if isinstance(document, dict) else document
    if not isinstance(rows, list) or not rows:
        die("expected a non-empty list under 'snapshots'")
    return rows


def word(value):
    return value.strip() if isinstance(value, str) else ""


def stamp(value, label):
    if not isinstance(value, str) or not value.strip():
        die("%s is not an ISO timestamp" % label)
    raw = value.strip()
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        die("%s is not an ISO timestamp: %s" % (label, value))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def size_of(row, label):
    value = row.get("size_gb", row.get("size"))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        die("%s.size_gb must be a number of GiB" % label)
    if value < 0:
        die("%s.size_gb cannot be negative" % label)
    return float(value)


def parse(rows):
    out = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            die("snapshot %d is not an object" % index)
        sid = word(row.get("id"))
        if not sid:
            die("snapshot %d has no id" % index)
        status = word(row.get("status")).lower()
        if not status:
            die("%s has no status" % sid)
        out.append({"id": sid,
                    "taken": stamp(row.get("taken_at"), "%s.taken_at" % sid),
                    "status": status,
                    "size": size_of(row, sid)})
    return out


def human_age(minutes):
    if minutes < 60:
        return "%dm" % minutes
    return "%dh%02dm" % (minutes // 60, minutes % 60)


def command_for(args, snapshot):
    if args.provider == "aws":
        return ("aws ec2 create-volume --snapshot-id %s "
                "--availability-zone %s --volume-type gp3"
                % (snapshot["id"], args.az))
    if args.provider == "gcp":
        return ("gcloud compute disks create %s --source-snapshot %s"
                % (args.disk_name, snapshot["id"]))
    return ("az disk create -n %s --source %s"
            % (args.disk_name, snapshot["id"]))


def main():
    parser = argparse.ArgumentParser(
        description="Pick the newest restorable snapshot before an incident "
                    "and print the provider's restore command.")
    parser.add_argument("catalog", nargs="?", default="-",
                        help="backup catalog JSON; stdin when omitted")
    parser.add_argument("-i", "--incident", required=True,
                        help="ISO timestamp of the incident")
    parser.add_argument("--window", type=float, default=6.0,
                        help="hours before the incident to search (default 6)")
    parser.add_argument("-p", "--provider", choices=("aws", "gcp", "az"),
                        default="aws", help="restore command family (default aws)")
    parser.add_argument("--az", default="ZONE",
                        help="availability zone for the aws command")
    parser.add_argument("--disk-name", default="restore",
                        help="disk name for the gcp and az commands")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    if args.window <= 0:
        die("--window must be greater than zero")
    if not args.disk_name.strip():
        die("--disk-name cannot be empty")

    incident = stamp(args.incident, "--incident")
    snapshots = parse(rows_of(load(args.catalog)))
    snapshots.sort(key=lambda s: s["taken"], reverse=True)
    print("INCIDENT %s, window %gh"
          % (incident.strftime("%Y-%m-%dT%H:%M:%SZ"), args.window))

    candidates = []
    for snapshot in snapshots:
        age = (incident - snapshot["taken"]).total_seconds()
        if age < 0:
            print("SKIP %s taken after the incident" % snapshot["id"])
            continue
        if age > args.window * 3600:
            continue
        if snapshot["status"] not in RESTORABLE:
            reason = ("status=" + snapshot["status"]
                      if snapshot["status"] in KNOWN_BAD
                      else "unknown status=" + snapshot["status"])
            print("SKIP %s %s" % (snapshot["id"], reason))
            continue
        if snapshot["size"] <= 0:
            print("SKIP %s size=0" % snapshot["id"])
            continue
        candidates.append(snapshot)

    if not candidates:
        print("CHECK 0 candidates in the %gh before the incident" % args.window)
        print("FAIL no restorable point; widen --window or check the backup job")
        return 1

    for snapshot in candidates:
        minutes = int((incident - snapshot["taken"]).total_seconds() // 60)
        print("CANDIDATE %s %s %s %.0fGiB, %s before"
              % (snapshot["id"],
                 snapshot["taken"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                 snapshot["status"], snapshot["size"], human_age(minutes)))

    best = candidates[0]
    minutes = int((incident - best["taken"]).total_seconds() // 60)
    print("OK newest restorable %s, %s before the incident"
          % (best["id"], human_age(minutes)))
    print("RESTORE %s %.0fGiB taken %s"
          % (best["id"], best["size"],
             best["taken"].strftime("%Y-%m-%dT%H:%M:%SZ")))
    print("COMMAND " + command_for(args, best))
    return 0


if __name__ == "__main__":
    sys.exit(main())
