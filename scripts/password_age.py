#!/usr/bin/env python3
"""password_age.py - audit a passwd/shadow export without printing hashes.

Reads a colon-separated shadow export and reports four things: an empty
password field (a login with no password), an account with no expiry date,
a password older than --max-days, and a last-change field that cannot be
aged. A passwd-format line (seven fields) is accepted for the empty-field
check only; its aging data lives in shadow.

Shadow fields: name:hash:lastchg:min:max:warn:inactive:expire:reserved.
lastchg and expire are days since 1 January 1970. Locked entries (a hash
starting with ! or *) are skipped unless --include-locked is given, because
a locked system account is not a password risk.

Usage:
    python3 password_age.py shadow.txt
    python3 password_age.py shadow.txt --max-days 60
    python3 password_age.py shadow.txt --include-locked
    python3 password_age.py shadow.txt --now 2026-10-21
    python3 password_age.py --help

CI (fail when a privileged account is past the policy):
    python3 password_age.py /etc/shadow --max-days 90 || exit 1

Cron (weekly, before the access review):
    0 6 * * 1 python3 /opt/s0sta/password_age.py /etc/shadow --max-days 90

Exit codes: 0 no finding, 1 at least one finding, 2 usage error or
unreadable, empty or malformed input.

Read-only: the export is opened for reading only. Nothing is locked, reset
or written and no network call is made. The password hash is never printed,
stored or used as anything but a yes/no answer about emptiness and locking;
the report names the account and the age, never the hash.

By s0sta.com
"""
import argparse
import sys
from datetime import date

EPOCH = date(1970, 1, 1)


class InputError(Exception):
    """An input that cannot be audited."""


def parse_day(text):
    """Parse an ISO 8601 date used by --now."""
    try:
        return date.fromisoformat(text.strip()[:10])
    except (AttributeError, ValueError):
        raise InputError("--now is not an ISO 8601 date: %r" % text)


def read_lines(path):
    """Return the non-blank, non-comment lines of a colon file."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise InputError("%s: not text" % path)
    entries = [(number, line.rstrip("\n"))
               for number, line in enumerate(lines, start=1)
               if line.strip() and not line.lstrip().startswith("#")]
    if not entries:
        raise InputError("%s: empty input" % path)
    return entries


def audit(path, max_days, include_locked, today):
    """Return (findings, accounts, notes) for one colon export."""
    findings = []
    accounts = 0
    passwd_lines = 0
    for number, line in read_lines(path):
        fields = line.split(":")
        if len(fields) < 7:
            raise InputError("line %d: expected at least 7 fields" % number)
        name = fields[0].strip()
        if not name:
            raise InputError("line %d: empty account name" % number)
        accounts += 1
        if len(fields) == 7:
            passwd_lines += 1
            if fields[1] == "":
                findings.append("EMPTY %s (no password field)" % name)
            continue
        password = fields[1]
        if password == "":
            findings.append("EMPTY %s (no password field)" % name)
        if password.startswith(("!", "*")) and not include_locked:
            continue
        if not fields[7].strip():
            findings.append("NOEXP %s (no account expiry)" % name)
        raw = fields[2].strip()
        if raw == "0":
            findings.append("FORCE %s (lastchg 0, change at next login)" % name)
        elif not raw.isdigit():
            findings.append("NOAGE %s (no usable last-change field)" % name)
        else:
            age = (today - EPOCH).days - int(raw)
            if age < 0:
                findings.append("FUTURE %s (last change is in the future)" % name)
            elif age > max_days:
                findings.append("OLD %s %dd (max %dd)" % (name, age, max_days))
    notes = []
    if passwd_lines:
        notes.append("%d passwd-format line(s): empty field checked, age and "
                     "expiry need the shadow file" % passwd_lines)
    return findings, accounts, notes


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Audit a passwd/shadow export for weak password age.")
    parser.add_argument("export", help="colon-separated passwd or shadow export")
    parser.add_argument("--max-days", type=int, default=90,
                        help="flag passwords older than this (default 90)")
    parser.add_argument("--include-locked", action="store_true",
                        help="also check entries whose hash starts with ! or *")
    parser.add_argument("--now", help="ISO 8601 reference date (for testing)")
    args = parser.parse_args(argv)
    if args.max_days < 1:
        parser.error("--max-days must be a positive integer")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        today = parse_day(args.now) if args.now else date.today()
        findings, accounts, notes = audit(
            args.export, args.max_days, args.include_locked, today)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2
    for note in notes:
        print("NOTE %s" % note, file=sys.stderr)
    if findings:
        for finding in findings:
            print(finding)
        print("FINDING %d in %d account%s" % (
            len(findings), accounts, "" if accounts == 1 else "s"))
        return 1
    print("OK %d account%s, no weak password age" % (
        accounts, "" if accounts == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
