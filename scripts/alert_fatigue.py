#!/usr/bin/env python3
"""Rank alert rules by how rarely an alert leads to an action.

Reads an alert history and computes one number per rule:

    signal ratio = actioned alerts / alerts fired

A rule that fires fifty times and is actioned twice has a ratio of 0.04. It
is not an alert, it is a habit. The tool ranks rules from the noisiest up and
exits 1 when any rule with enough fires falls below --threshold.

The history is JSON, one object per alert:

    [{"rule": "login-failed", "fired_at": "2026-10-20T03:14:00Z",
      "actioned": false},
     {"rule": "checkout-latency", "fired_at": "2026-10-20T09:02:00Z",
      "actioned": true}]

"actioned" means a human did something because of the alert: acknowledged
and fixed, or acknowledged and closed as expected. An alert that was seen and
ignored is not actioned.

A rule needs --min-fired alerts (default 5) before it is judged. The window
is all history by default; --days N looks at the last N days. The threshold
is a minimum acceptable signal ratio, 0.10 by default.

Usage:
    python3 alert_fatigue.py alerts.json
    python3 alert_fatigue.py alerts.json --threshold 0.20 --days 30

Exit codes: 0 no rule below the threshold, 1 at least one noisy rule, 2
usage, or a history that is missing, unreadable, invalid or empty.

CI (monthly review, fail when the pager is mostly noise):
    python3 alert_fatigue.py alerts.json --days 30 || exit 1

Cron (Monday 08:00, send the noise ranking to the on-call lead):
    0 8 * * 1 python3 /opt/s0sta/alert_fatigue.py /var/lib/s0sta/alerts.json

The script is read-only. It reads the export and prints a ranking; it never
silences, edits or deletes a rule. A low ratio can also mean the alert is
correct but the runbook is bad: read the actions before you delete the rule.

Standard library only, Python 3.8+.

By s0sta.com
"""
import argparse
import datetime
import json
import sys


class InputError(Exception):
    """Anything that should end the run with exit code 2."""


def load_history(path):
    """Return the list of alert events, or raise InputError."""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise InputError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(doc, list) or not doc:
        raise InputError("%s has no non-empty alert list" % path)
    return doc


def event_fields(item, number):
    """Validate one alert event and return (rule, date, actioned)."""
    if not isinstance(item, dict):
        raise InputError("event %d is not an object" % number)
    rule = item.get("rule")
    fired_at = item.get("fired_at")
    actioned = item.get("actioned")
    if not isinstance(rule, str) or not rule:
        raise InputError("event %d has no rule" % number)
    if not isinstance(fired_at, str) or len(fired_at) < 10:
        raise InputError("event %s has no fired_at timestamp" % rule)
    try:
        when = datetime.date.fromisoformat(fired_at[:10])
    except ValueError:
        raise InputError("event %s has an unreadable fired_at: %s"
                         % (rule, fired_at))
    if not isinstance(actioned, bool):
        raise InputError("event %s has no boolean actioned" % rule)
    return rule, when, actioned


def ratio(value):
    """argparse type for a signal ratio between 0 and 1."""
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not a number" % value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("%s is outside 0..1" % value)
    return number


def positive(value):
    """argparse type for a positive integer."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not an integer" % value)
    if number < 1:
        raise argparse.ArgumentTypeError("%s is less than 1" % value)
    return number


def nonneg(value):
    """argparse type for a non-negative integer."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not an integer" % value)
    if number < 0:
        raise argparse.ArgumentTypeError("%s is negative" % value)
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank alert rules by signal ratio and exit 1 when the "
                    "pager is mostly noise.",
        epilog="Exit codes: 0 quiet enough, 1 noisy rule found, "
               "2 usage or input error.")
    parser.add_argument("history", help="JSON list of alert events")
    parser.add_argument("--threshold", type=ratio, default=0.10,
                        help="minimum signal ratio (default: 0.10)")
    parser.add_argument("--min-fired", type=positive, default=5,
                        help="fires before a rule is judged (default: 5)")
    parser.add_argument("--days", type=nonneg, default=0,
                        help="only the last N days (default: all history)")
    parser.add_argument("--top", type=positive, default=20,
                        help="maximum noisy rules to print (default: 20)")
    args = parser.parse_args(argv)

    try:
        history = load_history(args.history)
        cutoff = None
        if args.days:
            cutoff = datetime.date.today() - datetime.timedelta(days=args.days)
        counts = {}
        in_window = 0
        for number, item in enumerate(history, 1):
            rule, when, actioned = event_fields(item, number)
            if cutoff is not None and when < cutoff:
                continue
            in_window += 1
            fired, acted = counts.get(rule, (0, 0))
            counts[rule] = (fired + 1, acted + int(actioned))
        if not in_window:
            raise InputError("no alert events in the last %d days" % args.days)
    except InputError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2

    noisy = []
    for rule, (fired, acted) in counts.items():
        if fired < args.min_fired:
            continue
        signal = acted / fired
        if signal < args.threshold:
            noisy.append((signal, -fired, rule, fired, acted))
    noisy.sort()

    if noisy:
        print("FINDING %d noisy rules of %d" % (len(noisy), len(counts)))
        for signal, _, rule, fired, acted in noisy[:args.top]:
            print("NOISE %s ratio %.2f fired %d actioned %d"
                  % (rule, signal, fired, acted))
        return 1
    print("OK every judged rule is at or above %.2f signal" % args.threshold)
    return 0


if __name__ == "__main__":
    sys.exit(main())
