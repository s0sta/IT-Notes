#!/usr/bin/env python3
"""alert_dedupe.py - group duplicate alerts into incidents and rank noisy rules.

Incident-response teams do not drown in incidents. They drown in pages: the
same failing disk sends a new webhook every five minutes, with a new alert id
and the same fingerprint. This script reads the raw alert payloads, groups
them by fingerprint, and reports the incidents behind the alerts.

The input is a JSON list, or an object with an "alerts" list. Each alert is:

    {"fingerprint": "fp-disk-var",
     "rule": "DiskFull",
     "severity": "critical",
     "started_at": "2026-10-20T03:02:10Z",
     "status": "firing"}

status is one of firing, acknowledged, resolved or suppressed. Severity is
one of critical, high, medium or low. The fingerprint is the dedupe key and
must be stable across repeats; rule plus host plus symptom is a good start.

The report is a list of incidents, a ranking of the noisiest rules, and one
line naming the rules over --max-fires. Exit 1 is the finding: a rule is
paging more often than the budget allows.

Usage:
    python3 alert_dedupe.py alerts.json
    python3 alert_dedupe.py alerts.json --max-fires 3
    cat alerts.json | python3 alert_dedupe.py -
    python3 alert_dedupe.py --help

Cron or CI (hourly, fail the job when a rule is over budget):
    5 * * * * python3 /opt/s0sta/alert_dedupe.py /var/lib/s0sta/alerts.json --max-fires 3

Exit codes: 0 no rule over the threshold, 1 at least one rule over the
threshold, 2 usage error or unreadable, empty or malformed input.

Read-only: opens the given file or stdin, parses JSON and prints. It writes
nothing, changes nothing and makes no network call.

By s0sta.com
"""
import argparse
import json
import sys
from datetime import datetime, timezone

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATUSES = ("firing", "acknowledged", "resolved", "suppressed")
DEFAULT_MAX_FIRES = 3
DEFAULT_TOP = 5


class InputError(Exception):
    """An input that cannot be read as alert data."""


def read_json(path):
    """Return the decoded JSON document, or raise InputError."""
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    if not text.strip():
        raise InputError("%s: empty input" % path)
    try:
        return json.loads(text)
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))


def parse_time(value, where):
    """Return an aware UTC datetime, or raise InputError."""
    if not isinstance(value, str) or not value.strip():
        raise InputError("%s: started_at must be an ISO timestamp" % where)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        raise InputError("%s: bad started_at %r" % (where, value))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc)


def load_alerts(path):
    """Return a validated list of alert dicts, or raise InputError."""
    doc = read_json(path)
    if isinstance(doc, dict):
        if "alerts" not in doc:
            raise InputError("%s: object needs an \"alerts\" list" % path)
        doc = doc["alerts"]
    if not isinstance(doc, list):
        raise InputError("%s: expected a list of alerts" % path)
    if not doc:
        raise InputError("%s: no alerts in input" % path)
    alerts = []
    for index, raw in enumerate(doc, start=1):
        where = "alert %d" % index
        if not isinstance(raw, dict):
            raise InputError("%s: expected an object" % where)
        fingerprint = raw.get("fingerprint")
        rule = raw.get("rule")
        severity = raw.get("severity")
        status = raw.get("status")
        if not isinstance(fingerprint, str) or not fingerprint.strip():
            raise InputError("%s: missing fingerprint" % where)
        if not isinstance(rule, str) or not rule.strip():
            raise InputError("%s: missing rule" % where)
        if not isinstance(severity, str) or severity.lower() not in SEVERITY_RANK:
            raise InputError("%s: severity must be critical, high, medium or low"
                             % where)
        if not isinstance(status, str) or status.lower() not in STATUSES:
            raise InputError("%s: status must be one of %s"
                             % (where, ", ".join(STATUSES)))
        alerts.append({
            "fingerprint": fingerprint.strip(),
            "rule": rule.strip(),
            "severity": severity.lower(),
            "status": status.lower(),
            "started": parse_time(raw.get("started_at"), where),
        })
    return alerts


def group_alerts(alerts):
    """Return incidents keyed by fingerprint, earliest first."""
    groups = {}
    for alert in alerts:
        key = alert["fingerprint"]
        group = groups.get(key)
        if group is None:
            group = {
                "fingerprint": key,
                "rule": alert["rule"],
                "severity": alert["severity"],
                "first": alert["started"],
                "last": alert["started"],
                "count": 0,
                "statuses": set(),
            }
            groups[key] = group
        group["count"] += 1
        group["statuses"].add(alert["status"])
        if alert["started"] < group["first"]:
            group["first"] = alert["started"]
        if alert["started"] > group["last"]:
            group["last"] = alert["started"]
        if SEVERITY_RANK[alert["severity"]] < SEVERITY_RANK[group["severity"]]:
            group["severity"] = alert["severity"]
            group["rule"] = alert["rule"]
    return sorted(groups.values(), key=lambda g: (g["first"], g["fingerprint"]))


def rank_rules(alerts):
    """Return per-rule counts, incidents and worst severity, noisiest first."""
    rules = {}
    for alert in alerts:
        entry = rules.setdefault(alert["rule"], {
            "fires": 0,
            "incidents": set(),
            "worst": alert["severity"],
        })
        entry["fires"] += 1
        entry["incidents"].add(alert["fingerprint"])
        if SEVERITY_RANK[alert["severity"]] < SEVERITY_RANK[entry["worst"]]:
            entry["worst"] = alert["severity"]
    ordered = sorted(
        rules.items(),
        key=lambda item: (-item[1]["fires"], SEVERITY_RANK[item[1]["worst"]],
                          item[0]),
    )
    return ordered


def report(alerts, max_fires, top):
    """Return (finding, lines) for the alert payload."""
    groups = group_alerts(alerts)
    ranked = rank_rules(alerts)
    duplicates = len(alerts) - len(groups)
    lines = ["DEDUPE %d alert%s -> %d incident%s (%d duplicate%s)"
             % (len(alerts), "" if len(alerts) == 1 else "s",
                len(groups), "" if len(groups) == 1 else "s",
                duplicates, "" if duplicates == 1 else "s")]
    for group in groups:
        lines.append(
            "GROUP %-22s %-12s %d alert%s %s -> %s"
            % (group["fingerprint"], group["rule"], group["count"],
               "" if group["count"] == 1 else "s",
               group["first"].strftime("%H:%M:%S"),
               group["last"].strftime("%H:%M:%S")))
    for place, (rule, entry) in enumerate(ranked[:top], start=1):
        incidents = len(entry["incidents"])
        lines.append(
            "RANK %d %-16s %d fire%s, %d incident%s, worst %s"
            % (place, rule, entry["fires"],
               "" if entry["fires"] == 1 else "s",
               incidents, "" if incidents == 1 else "s", entry["worst"]))
    noisy = [(rule, entry) for rule, entry in ranked
             if entry["fires"] > max_fires]
    if not noisy:
        lines.append("NOISE none over %d fires" % max_fires)
    elif len(noisy) == 1:
        rule, entry = noisy[0]
        lines.append("NOISE rule %s %d fires, worst %s"
                     % (rule, entry["fires"], entry["worst"]))
    else:
        lines.append("NOISE %d rules over %d fires: %s"
                     % (len(noisy), max_fires,
                        ", ".join("%s (%d)" % (rule, entry["fires"])
                                  for rule, entry in noisy)))
    return bool(noisy), lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Group duplicate alerts by fingerprint (read-only).")
    parser.add_argument(
        "alerts", nargs="?", default="-",
        help="alert payload JSON, or - for stdin (default: -)")
    parser.add_argument(
        "--max-fires", type=int, default=DEFAULT_MAX_FIRES, metavar="N",
        help="exit 1 when a rule fires more than N times (default: %d)"
             % DEFAULT_MAX_FIRES)
    parser.add_argument(
        "--top", type=int, default=DEFAULT_TOP, metavar="N",
        help="rank at most N rules (default: %d)" % DEFAULT_TOP)
    args = parser.parse_args(argv)

    if args.max_fires < 0:
        parser.error("--max-fires must not be negative")
    if args.top < 1:
        parser.error("--top must be at least 1")

    try:
        alerts = load_alerts(args.alerts)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    finding, lines = report(alerts, args.max_fires, args.top)
    for line in lines:
        print(line)
    return 1 if finding else 0


if __name__ == "__main__":
    sys.exit(main())
