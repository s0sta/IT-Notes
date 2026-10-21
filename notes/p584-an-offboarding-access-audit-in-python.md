---
id: p584
title: "An offboarding access audit in Python"
slug: an-offboarding-access-audit-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Identity, CyberSecurity, DevSecOps, Automation]
source: "LinkedIn post P584 · PythonFixes series"
linkedin_date: 2030-06-20
design: code
script: offboarding_audit.py
---

# An offboarding access audit in Python

A contractor's last day was 30 September. On 5 October the GitHub account was still active, and the last login was three days after the farewell message.

## Quick reference

The full script is at the end of this note: `offboarding_audit.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 offboarding_audit.py leavers.json access.json
```

**Example output**

```text
USED ana@example.com github
USED sam@example.com vpn
```

## Explained

### What it does

It joins an HR leavers export to an access export on the email address. An account whose kind is active or enabled after the last day is ACTIVE. A last_login after that day is USED, even when the account is marked disabled elsewhere. On screen the join prints USED ana@example.com github and USED sam@example.com vpn, then exits 1.

### How to run it

`python3 offboarding_audit.py leavers.json access.json`. `--grace-days 2` allows a handover window. Run it when HR closes a leaver ticket, and again from cron every morning as a safety net for the feed that never arrived.

### The fix

Disable each flagged account, revoke its sessions and tokens, then run the audit again until it prints OK. Check the identity provider as well as the application: disabling the SSO account does not always disable the token that was issued before it.

### Prevention

Make the HR event the trigger, not a quarterly review. The access export must name every system, including the local ones that no SSO log covers. One owner per system is what makes the export complete.

> **The honest caveat:** the audit only sees the systems in the export. A shared password or a local account on a build host can outlive the leaver without appearing in either file.

> **The lesson:** offboarding ends when access ends, not when the ticket closes.

## In one line

> **Offboarding ends when access ends.** The ticket closes on the last day; the account does not.

**Check the join**

```bash
python3 offboarding_audit.py lv.json ac.json
```

## Script: offboarding_audit.py

Download: [scripts/offboarding_audit.py](../scripts/offboarding_audit.py)

```python
#!/usr/bin/env python3
"""offboarding_audit.py - find accounts a leaver can still use.

Joins an HR leavers export to an access export and reports accounts that are
still active after the person's last day, or were used after it. The join is
the part most offboarding checks miss: HR knows the date, the systems know the
account, and nobody puts the two files side by side.

Leavers shape (a bare list also works):

    {"leavers": [
      {"email": "ana@example.com", "last_day": "2026-09-30"},
      {"email": "sam@example.com", "last_day": "2026-10-15"}
    ]}

Access shape (a bare list also works):

    {"accounts": [
      {"user": "ana@example.com", "system": "github",
       "last_login": "2026-10-05T10:00:00Z", "kind": "active"},
      {"user": "sam@example.com", "system": "vpn",
       "last_login": null, "kind": "disabled"}
    ]}

kind active or enabled counts as open; any other value counts as disabled,
but a login after the last day is still reported.

Usage:
    python3 offboarding_audit.py leavers.json access.json
    python3 offboarding_audit.py leavers.json access.json --grace-days 2
    python3 offboarding_audit.py leavers.json access.json --now 2026-10-21
    python3 offboarding_audit.py --help

CI (run on every leaver event, not once a quarter):
    python3 offboarding_audit.py leavers.json access.json || exit 1

Cron (daily safety net for the HR feed):
    0 6 * * * python3 /opt/s0sta/offboarding_audit.py /etc/s0sta/leavers.json /etc/s0sta/access.json

Exit codes: 0 no account outlives its owner's last day, 1 at least one
finding, 2 usage error or unreadable, invalid or empty input.

Read-only: both files are opened for reading. Nothing is disabled, revoked
or written and no network call is made. Reports name the account and the
system, never a token, password or session value.

By s0sta.com
"""
import argparse
import json
import sys
from datetime import date, timedelta

OPEN_KINDS = ("active", "enabled")


class InputError(Exception):
    """An input that cannot be audited."""


def load_list(path, key):
    """Return the list under key (or the document itself), or raise."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InputError("%s: not valid JSON: %s" % (path, exc))
    if isinstance(document, dict):
        records = document.get(key)
    else:
        records = document
    if not isinstance(records, list):
        raise InputError("%s: expected a list or an object with a %s list"
                         % (path, key))
    return records


def parse_day(value, where, field):
    """Parse an ISO 8601 date or timestamp's date part."""
    if not isinstance(value, str) or len(value.strip()) < 10:
        raise InputError("%s: %s is not an ISO 8601 date" % (where, field))
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        raise InputError("%s: %s is not an ISO 8601 date: %r"
                         % (where, field, value))


def load_leavers(path):
    """Return {email: last_day} and the number of records."""
    records = load_list(path, "leavers")
    leavers = {}
    for index, record in enumerate(records):
        where = "leaver %d" % (index + 1)
        if not isinstance(record, dict):
            raise InputError("%s is not an object" % where)
        email = record.get("email")
        if not isinstance(email, str) or not email.strip():
            raise InputError("%s: email is missing" % where)
        leavers[email.strip().lower()] = parse_day(
            record.get("last_day"), where, "last_day")
    return leavers


def load_accounts(path):
    """Return a list of (user, system, last_login date or None, kind)."""
    records = load_list(path, "accounts")
    accounts = []
    for index, record in enumerate(records):
        where = "account %d" % (index + 1)
        if not isinstance(record, dict):
            raise InputError("%s is not an object" % where)
        for field in ("user", "system"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise InputError("%s: %s is missing" % (where, field))
        last = record.get("last_login")
        if last is not None:
            last = parse_day(last, where, "last_login")
        kind = record.get("kind", "active")
        if not isinstance(kind, str):
            raise InputError("%s: kind must be a string" % where)
        accounts.append((record["user"].strip().lower(),
                         record["system"].strip(), last, kind.strip().lower()))
    return accounts


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Join leavers to access and report surviving accounts.")
    parser.add_argument("leavers", help="HR leavers JSON")
    parser.add_argument("accounts", help="access export JSON")
    parser.add_argument("--grace-days", type=int, default=0,
                        help="days of access allowed after the last day")
    parser.add_argument("--now", help="ISO 8601 reference date (for testing)")
    args = parser.parse_args(argv)
    if args.grace_days < 0:
        parser.error("--grace-days must not be negative")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        leavers = load_leavers(args.leavers)
        accounts = load_accounts(args.accounts)
        if args.now:
            today = parse_day(args.now, "arguments", "--now")
        else:
            today = date.today()
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    seen = {email: 0 for email in leavers}
    findings = 0
    for user, system, last, kind in accounts:
        if user not in leavers:
            continue
        seen[user] += 1
        cutoff = leavers[user] + timedelta(days=args.grace_days)
        reasons = []
        if kind in OPEN_KINDS and today > cutoff:
            reasons.append("ACTIVE")
        if last is not None and last > cutoff:
            reasons.append("USED %s" % last.isoformat())
        if reasons:
            findings += 1
            print("%s %s %s (last day %s)"
                  % (", ".join(reasons), user, system, leavers[user].isoformat()))

    for email in sorted(leavers):
        if seen[email] == 0:
            print("CLEAR %s (no accounts in the export)" % email)

    if findings:
        print("FINDING %d of %d accounts outlive their last day"
              % (findings, len(accounts)))
        return 1
    print("OK %d leavers, %d accounts, none outlive their last day"
          % (len(leavers), len(accounts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
