#!/usr/bin/env python3
"""credential_rotate.py - plan a credential rotation in dependency order.

Reads a rotation registry and prints the order the secrets must be rotated in,
one STEP and one VERIFY line per secret. A secret's depends_on list names the
secrets that must be rotated before it, so a database root credential moves
before the application credential built on it.

Registry (metadata only; a value/token/key field is ignored and never read):

    {"secrets": [
      {"id": "db-root", "owner": "dba", "systems": ["db-01"],
       "depends_on": []},
      {"id": "api-db", "owner": "platform", "systems": ["api", "worker"],
       "depends_on": ["db-root"]},
      {"id": "jwt-key", "owner": "app", "systems": ["api"],
       "depends_on": ["api-db"]}
    ]}

A bare list of secrets also works. A cycle, an unknown dependency or a secret
with no owner is a finding. The script prints the plan; it does not rotate,
write or call a vault. The printed plan is the deliverable.

Usage:
    python3 credential_rotate.py rot.json
    python3 credential_rotate.py rot.json --json
    cat rot.json | python3 credential_rotate.py -

Cron (Monday morning, before the change window):
    0 6 * * 1 python3 /opt/s0sta/credential_rotate.py /etc/ir/rot.json \
      >> /var/log/ir/rotation.log 2>&1

CI (fail the job when the registry cannot be ordered):
    python3 credential_rotate.py /etc/ir/rot.json || exit 1

Exit codes: 0 the registry orders cleanly, 1 a cycle, an unknown dependency or
a secret with no owner, 2 usage error or unreadable, invalid or empty input.

Read-only: the registry is opened for reading only. No secret value is read or
printed, and no vault, cloud or API call is made. The registry holds ids,
owners, systems and dependencies; nothing here can rotate a credential. The
order is only as good as depends_on.

By s0sta.com
"""
import argparse
import json
import sys


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


def records(document):
    rows = document.get("secrets") if isinstance(document, dict) else document
    if not isinstance(rows, list) or not rows:
        die("expected a non-empty list under 'secrets'")
    return rows


def text(value):
    return value.strip() if isinstance(value, str) else ""


def names(value, label):
    if value is None:
        return []
    if not isinstance(value, list):
        die("%s must be a list" % label)
    out = []
    for item in value:
        name = text(item)
        if not name:
            die("%s must contain non-empty names" % label)
        out.append(name)
    return out


def parse(rows):
    secrets = {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            die("secret %d is not an object" % index)
        sid = text(row.get("id")) or text(row.get("secret"))
        if not sid:
            die("secret %d has no id" % index)
        if sid in secrets:
            die("duplicate secret id %s" % sid)
        owner = text(row.get("owner"))
        secrets[sid] = {
            "id": sid,
            "owner": owner or None,
            "systems": names(row.get("systems"), "%s.systems" % sid),
            "deps": names(row.get("depends_on"), "%s.depends_on" % sid),
        }
    return secrets


def find_cycle(secrets, remaining):
    """Return one cycle as a list with the start repeated at the end."""
    node = sorted(remaining)[0]
    path, seen = [], {}
    while node not in seen:
        seen[node] = len(path)
        path.append(node)
        next_nodes = sorted(set(secrets[node]["deps"]) & remaining)
        node = next_nodes[0] if next_nodes else path[0]
    return path[seen[node]:] + [node]


def order(secrets):
    remaining = set(secrets)
    result = []
    while remaining:
        ready = sorted(sid for sid in remaining
                       if not (set(secrets[sid]["deps"]) & remaining))
        if not ready:
            return result, find_cycle(secrets, remaining)
        result.extend(ready)
        remaining.difference_update(ready)
    return result, None


def main():
    parser = argparse.ArgumentParser(
        description="Plan a credential rotation in dependency order. Prints "
                    "the plan; it does not rotate anything.")
    parser.add_argument("registry", nargs="?", default="-",
                        help="rotation registry JSON; stdin when omitted")
    parser.add_argument("--json", action="store_true",
                        help="print the ordered plan as JSON")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    secrets = parse(records(load(args.registry)))

    findings = []
    for sid in sorted(secrets):
        for dep in secrets[sid]["deps"]:
            if dep not in secrets:
                findings.append("%s depends on unknown secret %s" % (sid, dep))

    if findings:
        for finding in findings:
            print("FINDING " + finding)
        print("PLAN blocked: fix the registry, then re-run")
        print("FAIL %d registry finding%s"
              % (len(findings), "" if len(findings) == 1 else "s"))
        return 1

    ordered, cycle = order(secrets)
    if cycle:
        print("FINDING cycle " + " -> ".join(cycle))
        print("PLAN blocked: break the cycle by hand, then re-run")
        print("FAIL no safe rotation order")
        return 1

    if args.json:
        ownerless = [sid for sid in ordered if not secrets[sid]["owner"]]
        print(json.dumps({
            "order": ordered,
            "steps": [{"id": sid, "owner": secrets[sid]["owner"],
                       "systems": secrets[sid]["systems"]} for sid in ordered],
            "ownerless": ownerless,
        }, indent=2))
        return 1 if ownerless else 0

    print("PLAN %d secret%s, %d step%s"
          % (len(ordered), "" if len(ordered) == 1 else "s",
             len(ordered), "" if len(ordered) == 1 else "s"))
    for number, sid in enumerate(ordered, 1):
        item = secrets[sid]
        owner = item["owner"] or "-"
        systems = ",".join(item["systems"]) or "-"
        print("STEP %d %s owner=%s systems=%s" % (number, sid, owner, systems))
        print("VERIFY %s on %s: new value accepted, old value rejected"
              % (sid, systems))

    print("ORDER " + " -> ".join(ordered))
    ownerless = [sid for sid in ordered if not secrets[sid]["owner"]]
    if ownerless:
        for sid in ownerless:
            print("FINDING %s has no owner" % sid)
        print("FAIL %d secret%s %s an owner"
              % (len(ownerless), "" if len(ownerless) == 1 else "s",
                 "needs" if len(ownerless) == 1 else "need"))
        return 1
    print("OK %d secret%s in order, %d verify step%s"
          % (len(ordered), "" if len(ordered) == 1 else "s",
             len(ordered), "" if len(ordered) == 1 else "s"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
