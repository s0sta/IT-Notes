#!/usr/bin/env python3
"""kill_switch_audit.py - rank the flags that gate one service before a rollback.

Reads a feature-flag export, finds every flag that gates the named service, and
checks the two things a kill switch needs at 03:00: an owner and a default. The
flags are ranked by blast radius, the traffic share multiplied by the number of
services that read the flag, so the first line is the one to pull first.

Read-only: it prints the audit and writes nothing. A flag without an owner is a
finding, not a warning: nobody can approve pulling it.

Usage:
  ./kill_switch_audit.py flags.json --service checkout
  ./kill_switch_audit.py flags.json --service checkout --env prod
  ./kill_switch_audit.py flags.json --service checkout --min-blast 10

Cron / CI (weekly, fails while a flag has no owner):
  0 6 * * 1 /usr/local/bin/kill_switch_audit.py /etc/ir/flags.json \
    --service checkout >> /var/log/ir/flags.log 2>&1

Exit codes:
  0  every flag in scope has an owner and a default
  1  at least one flag in scope has no owner or no default
  2  usage error, unreadable JSON, bad traffic value, or no flags for service

Flags: {"service": "checkout",
        "flags": [{"key": "checkout.payments-v2", "owner": "payments",
                   "default": false, "traffic": 35,
                   "dependents": ["cart", "orders"]}, ...]}

By s0sta.com
"""
import argparse
import json
import sys


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


def blast(traffic, dependents):
    return traffic * max(1, len(dependents))


def main():
    ap = argparse.ArgumentParser(
        description="Audit the feature flags that gate a service: owner, "
                    "default and blast radius.")
    ap.add_argument("flags", help="feature-flag export JSON")
    ap.add_argument("--service", required=True, help="service to audit")
    ap.add_argument("--env", default=None,
                    help="only flags that apply to this environment")
    ap.add_argument("--min-blast", type=int, default=0,
                    help="only flags with a blast radius of at least this")
    ap.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = ap.parse_args()

    if args.min_blast < 0:
        die("--min-blast must be zero or more")

    doc = load(args.flags)
    if not isinstance(doc, dict):
        die("export: expected a JSON object")
    flags = doc.get("flags") or []
    if not isinstance(flags, list):
        die("export: 'flags' must be a list")
    default_service = str(doc.get("service", "")).strip().lower()
    want = args.service.strip().lower()

    rows = []
    in_service = 0
    for f in flags:
        if not isinstance(f, dict):
            die("export: every flag must be an object")
        key = str(f.get("key", "")).strip()
        if not key:
            die("export: a flag has no key")
        service = str(f.get("service") or default_service).strip().lower()
        if service != want:
            continue
        in_service += 1
        raw_envs = f.get("environments") or []
        if not isinstance(raw_envs, list):
            die("flag %s: environments must be a list" % key)
        envs = [str(e).lower() for e in raw_envs]
        if args.env and args.env.lower() not in envs:
            continue
        owner = str(f.get("owner") or "").strip()
        has_default = isinstance(f.get("default"), bool)
        if f.get("default") is not None and "default" in f and not has_default:
            die("flag %s: default must be true or false" % key)
        try:
            traffic = float(f.get("traffic", 0))
        except (TypeError, ValueError):
            die("flag %s: traffic is not a number" % key)
        if not 0 <= traffic <= 100:
            die("flag %s: traffic must be 0-100" % key)
        deps = f.get("dependents") or []
        if not isinstance(deps, list):
            die("flag %s: dependents must be a list" % key)
        b = blast(traffic, deps)
        if b < args.min_blast:
            continue
        rows.append({"key": key, "owner": owner, "default": f.get("default"),
                     "has_default": has_default, "blast": int(b)})

    if not in_service:
        die("no flags gate service %s" % args.service)
    if not rows:
        print("OK no flags for %s match the filters" % args.service)
        return 0

    rows.sort(key=lambda r: (-r["blast"], r["key"]))
    print("PLAN kill-switch audit for %s, %d flag%s"
          % (args.service, len(rows), "" if len(rows) == 1 else "s"))
    no_owner = no_default = 0
    for r in rows:
        if not r["owner"]:
            no_owner += 1
            if not r["has_default"]:
                no_default += 1
            d = ("on" if r["default"] else "off") if r["has_default"] else "missing"
            print("NOOWNER %s blast %d default=%s" % (r["key"], r["blast"], d))
        elif not r["has_default"]:
            no_default += 1
            print("NODEFAULT %s blast %d owner=%s"
                  % (r["key"], r["blast"], r["owner"]))
        else:
            print("FLAG %s blast %d default=%s"
                  % (r["key"], r["blast"],
                     "on" if r["default"] else "off"))

    if no_owner or no_default:
        print("FINDING %d flag%s without an owner, %d without a default"
              % (no_owner, "" if no_owner == 1 else "s", no_default))
        sys.exit(1)
    print("READY %d flags, every one owned and defaulted" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
