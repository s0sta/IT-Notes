---
id: p683
title: "An ordered account lockout plan"
slug: an-ordered-account-lockout-plan
sections: [it, devsecops]
topic: "Python scripts"
tags: [IncidentResponse, Python, IAM, SRE, CyberSecurity]
source: "LinkedIn post P683 · IR series"
linkedin_date: 2031-02-06
design: code
script: account_lockout.py
---

# An ordered account lockout plan

The identity is compromised. The first instinct is to disable every account carrying the email, including the shared build account four teams deploy through.

## Quick reference

The full script is at the end of this note: `account_lockout.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 account_lockout.py identity.json
```

**Example output**

```text
LOCK 3 systems in order: okta, aws, github
HOLD jenkins build shared, owner unknown
```

## Explained

### What it does

`account_lockout.py` reads an identity export: systems with a tier and a kind, accounts with a login, a shared flag and a break-glass flag. It matches the identity, sorts accounts by tier, and prints the plan in dependency order. The identity provider comes first because it ends the sessions; cloud, source control and CI follow.

### What the screen shows

The panel sorts four accounts and prints LOCK 3 systems in order: okta, aws, github, then HOLD jenkins build shared, owner unknown. Exit 1 means a human must decide.

### How to run it

`python3 account_lockout.py identity.json --identity ana@example.com`, or let the export name the identity. `--min-tier 2` skips the identity provider when the sessions are gone. Pipe it into the ticket; it writes nothing.

### The fix

Disable the IdP account first, so the next sign-in fails, then revoke cloud keys, then block source control and CI. Hold the shared account, rotate the secret it uses, and tell its owner. A break-glass account goes to the incident commander, not to the script.

### Prevention

Give every account an owner field, keep a break-glass register, and audit both quarterly. An export with no owner column cannot produce this plan.

> **The honest caveat:** the export is a snapshot, and a token issued after it was taken is invisible.

> **The lesson:** the account is the access; the person is the witness.

## In one line

> **End the access, not the human.** A shared account is a team's access: hold it, rotate what it reaches.

**Order the locks**

```bash
python3 account_lockout.py identity.json
```

## Script: account_lockout.py

Download: [scripts/account_lockout.py](../scripts/account_lockout.py)

```python
#!/usr/bin/env python3
"""account_lockout.py - plan a compromised identity lockout in dependency order.

Reads an identity export and a compromised identity, then prints the
disable/revoke plan in the order the systems depend on each other: the identity
provider first, because it ends the sessions, then cloud roles, source control
and CI, then everything else. A shared or break-glass account is held for a
human decision, never disabled by the plan.

Read-only: it prints the plan, writes nothing and calls no provider API. The
printed lines are the deliverable for the incident ticket.

Usage:
  ./account_lockout.py identity.json --identity ana@example.com
  ./account_lockout.py identity.json --identity ana@example.com --min-tier 2
  ./account_lockout.py identity.json          # identity from the export

Cron / CI (incident job, not a schedule):
  ./account_lockout.py /etc/ir/identity.json \
    --identity "$(cat /tmp/ir/compromised)" | tee /var/log/ir/lockout.log

Exit codes:
  0  plan complete, no shared or break-glass account in scope
  1  held: a shared or break-glass account needs a human decision first
  2  usage error, unreadable JSON, identity missing or no matching accounts

Identity export:
  {"identity": "ana@example.com",
   "systems": [{"name": "okta", "tier": 1, "kind": "idp"}, ...],
   "accounts": [{"system": "okta", "id": "00u1x",
                 "login": "ana@example.com", "shared": false,
                 "break_glass": false}, ...]}

By s0sta.com
"""
import argparse
import json
import sys

KINDS = {
    "idp": ("DISABLE", "deactivate, ends the sessions"),
    "cloud": ("REVOKE", "keys, roles and console access"),
    "scm": ("BLOCK", "tokens and login"),
    "ci": ("DISABLE", "the build account"),
    "other": ("DISABLE", "the account"),
}


def die(msg):
    print("ERROR " + msg, file=sys.stderr)
    sys.exit(2)


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        die("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        die("%s: not valid JSON (%s)" % (path, exc))


def main():
    ap = argparse.ArgumentParser(
        description="Print a compromised identity lockout plan in dependency "
                    "order, holding shared and break-glass accounts.")
    ap.add_argument("export", help="identity export JSON")
    ap.add_argument("--identity", default=None,
                    help="compromised identity (default: the export's identity)")
    ap.add_argument("--min-tier", type=int, default=0,
                    help="skip systems below this tier (default: 0, all)")
    ap.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = ap.parse_args()

    doc = load(args.export)
    if not isinstance(doc, dict):
        die("export: expected a JSON object")
    identity = (args.identity or doc.get("identity") or "").strip()
    if not identity:
        die("no identity: pass --identity or set 'identity' in the export")
    if args.min_tier < 0:
        die("--min-tier must be zero or more")

    systems = {}
    raw_systems = doc.get("systems") or []
    if not isinstance(raw_systems, list):
        die("export: systems must be a list")
    for s in raw_systems:
        if not isinstance(s, dict):
            die("export: every system must be an object")
        name = str(s.get("name", "")).strip()
        if not name:
            die("export: a system has no name")
        if name in systems:
            die("export: duplicate system %s" % name)
        try:
            tier = int(s.get("tier", 99))
        except (TypeError, ValueError):
            die("system %s: tier is not an integer" % name)
        kind = str(s.get("kind", "other")).lower()
        if kind not in KINDS:
            die("system %s: unknown kind %s" % (name, kind))
        systems[name] = (tier, kind)

    accounts = doc.get("accounts") or []
    if not isinstance(accounts, list):
        die("export: accounts must be a list")
    hits = []
    for a in accounts:
        if not isinstance(a, dict):
            die("export: every account must be an object")
        login = str(a.get("login") or a.get("user") or "").strip()
        if login.lower() != identity.lower():
            continue
        system = str(a.get("system", "")).strip()
        if system not in systems:
            die("account %s references unknown system %s"
                % (a.get("id", "?"), system or "(none)"))
        if not a.get("id"):
            die("account in %s has no id" % system)
        tier, kind = systems[system]
        if tier < args.min_tier:
            continue
        hits.append({
            "system": system,
            "id": str(a["id"]),
            "tier": tier,
            "kind": kind,
            "shared": bool(a.get("shared")),
            "break_glass": bool(a.get("break_glass")),
            "owner": str(a.get("owner") or "").strip(),
        })

    if not hits:
        die("no accounts for %s in %s" % (identity, args.export))

    hits.sort(key=lambda x: (x["tier"], x["system"], x["id"]))
    print("PLAN lock %s across %d system%s"
          % (identity, len(hits), "" if len(hits) == 1 else "s"))
    order = []
    for h in hits:
        if h["system"] not in order:
            order.append(h["system"])
    print("ORDER %s" % ", ".join("%s(%d)" % (s, systems[s][0]) for s in order))

    held = 0
    for h in hits:
        if h["break_glass"]:
            print("HOLD %s %s break-glass, confirm before disable"
                  % (h["system"], h["id"]))
            held += 1
            continue
        if h["shared"]:
            owner = h["owner"] or "unknown"
            print("HOLD %s %s shared, owner %s"
                  % (h["system"], h["id"], owner))
            held += 1
            continue
        verb, why = KINDS[h["kind"]]
        print("%s %s %s %s" % (verb, h["system"], h["id"], why))

    if held:
        print("FINDING %d held, resolve before disabling" % held)
        sys.exit(1)
    print("READY %d accounts in dependency order" % len(hits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
