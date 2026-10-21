#!/usr/bin/env python3
"""token_revoke.py - find every token an identity owns and print the revokes.

Reads a token inventory, selects the tokens for one user or one service, and
prints a revocation command for each one, oldest first. The inventory carries
id, owner, scopes, created and last_used; the script prints ids, ages and
scopes and never prints a value, secret or hash, even when the export contains
one.

Read-only: it prints the commands. It does not call a provider, and it does not
need the token value to revoke an AWS key or a Vault accessor.

Usage:
  ./token_revoke.py tokens.json --user ana@example.com
  ./token_revoke.py tokens.json --service ci-runner --stale-days 90

Cron / CI (weekly drift report, exits 1 while tokens exist):
  0 7 * * 1 /usr/local/bin/token_revoke.py /etc/ir/tokens.json \
    --user ana@example.com >> /var/log/ir/tokens.log 2>&1

Exit codes:
  0  no token matches
  1  at least one token matches and needs revocation
  2  usage error, unreadable JSON, bad date, or neither --user nor --service

Inventory:
  {"tokens": [{"id": "tok-11c", "system": "vault", "kind": "vault-token",
               "owner": "ana@example.com", "service": "ci-runner",
               "scopes": ["repo:read"], "created": "2024-05-01",
               "last_used": "2026-03-20"}, ...]}

By s0sta.com
"""
import argparse
import json
import sys
from datetime import date


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


def day(value, label):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        die("%s: not an ISO date: %s" % (label, value))


def age(d):
    if d is None:
        return None
    return max(0, (date.today() - d).days)


def main():
    ap = argparse.ArgumentParser(
        description="Print a revocation command for every token a user or "
                    "service owns. Values are never printed.")
    ap.add_argument("inventory", help="token inventory JSON")
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument("--user", help="owner to match")
    who.add_argument("--service", help="service to match")
    ap.add_argument("--stale-days", type=int, default=None,
                    help="only tokens unused for at least this many days")
    ap.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = ap.parse_args()

    if args.stale_days is not None and args.stale_days < 0:
        die("--stale-days must be zero or more")

    doc = load(args.inventory)
    rows = doc.get("tokens", doc) if isinstance(doc, dict) else doc
    if not isinstance(rows, list):
        die("inventory: expected a list under 'tokens'")

    want = (args.user or args.service or "").strip().lower()
    field = "owner" if args.user else "service"
    picked = []
    for t in rows:
        if not isinstance(t, dict):
            die("inventory: every token must be an object")
        if not t.get("id"):
            die("inventory: a token has no id")
        if str(t.get(field, "")).strip().lower() != want:
            continue
        created = day(t.get("created"), "created")
        used = day(t.get("last_used"), "last_used")
        if created is None:
            die("token %s: created is required" % t["id"])
        c_age = age(created)
        u_age = age(used)
        if args.stale_days is not None:
            if u_age is not None and u_age < args.stale_days:
                continue
        picked.append({
            "id": str(t["id"]),
            "system": str(t.get("system", "unknown")),
            "kind": str(t.get("kind", "other")),
            "owner": str(t.get("owner", "")),
            "scopes": [str(x) for x in (t.get("scopes") or [])],
            "created_age": c_age,
            "last_age": u_age,
            "principal": str(t.get("principal", "")),
        })

    picked.sort(key=lambda x: (-x["created_age"], x["id"]))
    print("PLAN revoke tokens for %s" % (args.user or args.service))
    if not picked:
        print("OK no tokens for %s" % (args.user or args.service))
        return 0

    for t in picked:
        last = "never" if t["last_age"] is None else "%dd" % t["last_age"]
        scopes = ",".join(t["scopes"]) or "-"
        print("REVOKE %s %s created=%dd last=%s scopes=%s"
              % (t["id"], t["system"], t["created_age"], last, scopes))
        if t["kind"] == "aws-key":
            print("CMD aws iam delete-access-key --user-name %s "
                  "--access-key-id %s" % (t["principal"] or t["owner"], t["id"]))
        elif t["kind"] == "vault-token":
            print("CMD vault token revoke -accessor %s" % t["id"])
        else:
            print("CMD no template for %s, revoke %s in the admin console"
                  % (t["kind"], t["id"]))

    print("REVOKE %d token%s for %s"
          % (len(picked), "" if len(picked) == 1 else "s",
             args.user or args.service))
    oldest = picked[0]
    last = "never" if oldest["last_age"] is None else "%dd" % oldest["last_age"]
    print("OLDEST %s %dd, last used %s"
          % (oldest["id"], oldest["created_age"], last))
    return 1


if __name__ == "__main__":
    sys.exit(main())
