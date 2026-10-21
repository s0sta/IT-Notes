#!/usr/bin/env python3
"""edge_block.py - add block rules at the edge without breaking an allow.

Reads the edge/WAF rule list and one or more IPs or CIDRs, then builds the
block rules that would be prepended to the list. Every request is checked
against the existing allow rules and against a protected list, because a block
placed first wins: a target that overlaps an allow silently disables it.

The default is a dry run: it prints the plan and writes nothing. --apply writes
the new rule list to a file; it refuses to write when any target conflicts, and
it never calls an edge API.

Usage:
  ./edge_block.py rules.json 198.51.100.7
  ./edge_block.py rules.json 203.0.113.0/25 198.51.100.7 --apply
  ./edge_block.py rules.json 198.51.100.7 --protect 10.0.0.0/8

Cron / CI (check a block request before the change window):
  ./edge_block.py /etc/edge/rules.json "$(cat /tmp/ir/block-list)" \
    | tee /var/log/ir/edge-block.log

Exit codes:
  0  no conflict; every target is new, duplicate or already blocked
  1  at least one conflict with an allow or a protected range
  2  usage error, unreadable JSON, bad CIDR, unknown action or duplicate id

Rules: {"rules": [{"id": "allow-partner", "action": "allow",
                   "cidr": "203.0.113.0/24"}, ...],
        "protect": ["198.51.100.10/32"]}

By s0sta.com
"""
import argparse
import ipaddress
import json
import os
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


def cidr(value, label):
    try:
        return ipaddress.ip_network(str(value), strict=False)
    except ValueError:
        die("%s: not an IP or CIDR: %s" % (label, value))


def main():
    ap = argparse.ArgumentParser(
        description="Build edge block rules and refuse targets that overlap "
                    "an allow or a protected range.")
    ap.add_argument("rules", help="edge/WAF rules JSON")
    ap.add_argument("targets", nargs="+", help="IPs or CIDRs to block")
    ap.add_argument("--protect", action="append", default=[],
                    help="address that must never be blocked (repeatable)")
    ap.add_argument("--apply", action="store_true",
                    help="write the new rule list; nothing is deployed")
    ap.add_argument("--out", default=None,
                    help="output path for --apply (default /tmp/edge-rules.json)")
    ap.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = ap.parse_args()

    doc = load(args.rules)
    if not isinstance(doc, dict):
        die("rules: expected a JSON object")
    rules = doc.get("rules") or []
    if not isinstance(rules, list):
        die("rules: 'rules' must be a list")
    seen_ids = set()
    allows, blocks = [], []
    for r in rules:
        if not isinstance(r, dict):
            die("rules: every rule must be an object")
        rid = str(r.get("id", "")).strip()
        if not rid:
            die("rules: a rule has no id")
        if rid in seen_ids:
            die("rules: duplicate id %s" % rid)
        seen_ids.add(rid)
        action = str(r.get("action", "")).lower()
        if action not in ("allow", "block"):
            die("rule %s: action must be allow or block" % rid)
        entry = (rid, cidr(r.get("cidr"), "rule %s cidr" % rid))
        (allows if action == "allow" else blocks).append(entry)

    protect = [cidr(p, "--protect") for p in args.protect]
    doc_protect = doc.get("protect") or []
    if not isinstance(doc_protect, list):
        die("rules: protect must be a list of CIDRs")
    protect += [cidr(p, "protect") for p in doc_protect]

    targets = []
    for t in args.targets:
        n = cidr(t, "target")
        if n not in targets:
            targets.append(n)
    targets.sort(key=lambda n: (int(n.network_address), n.prefixlen))

    print("PLAN block %d target%s before %d rules"
          % (len(targets), "" if len(targets) == 1 else "s", len(rules)))
    new_rules, conflicts, dups = [], 0, 0
    for t in targets:
        block_hit = None
        for rid, a in allows:
            if not t.overlaps(a):
                continue
            conflicts += 1
            if t.supernet_of(a) or t == a:
                print("CONFLICT %s shadows allow %s" % (t, rid))
            else:
                print("CONFLICT %s inside allow %s" % (t, rid))
            block_hit = rid
        for p in protect:
            if t.overlaps(p):
                conflicts += 1
                print("CONFLICT %s overlaps protected %s" % (t, p))
                block_hit = block_hit or "protect"
        covered = [rid for rid, b in blocks if t.subnet_of(b)]
        if covered and not block_hit:
            dups += 1
            print("DUP %s already blocked by %s" % (t, covered[0]))
            continue
        if block_hit:
            continue
        n = len(new_rules) + 1
        while "ir-block-%d" % n in seen_ids:
            n += 1
        nid = "ir-block-%d" % n
        seen_ids.add(nid)
        new_rules.append({"id": nid, "action": "block", "cidr": str(t),
                          "source": "edge_block"})
        print("BLOCK %s (new rule %s)" % (t, nid))

    if conflicts:
        print("FINDING %d conflict%s in %d target%s"
              % (conflicts, "" if conflicts == 1 else "s",
                 len(targets), "" if len(targets) == 1 else "s"))
        if args.apply:
            print("REFUSED --apply declined, no rule list written")
        sys.exit(1)
    print("READY %d new rule%s, %d duplicate%s, no conflict"
          % (len(new_rules), "" if len(new_rules) == 1 else "s",
             dups, "" if dups == 1 else "s"))

    if not args.apply:
        print("DRY-RUN nothing written. Add --apply to write the rule list.")
        return 0

    out = args.out or "/tmp/edge-rules.json"
    merged = {"rules": new_rules + rules}
    if protect:
        merged["protect"] = [str(p) for p in protect]
    try:
        fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.chmod(out, 0o600)
    except OSError as exc:
        die("%s: %s" % (out, exc.strerror or exc))
    print("WROTE %s mode 0600, %d rules" % (out, len(merged["rules"])))
    print("APPLY load %s into the edge rule set, then reload" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
