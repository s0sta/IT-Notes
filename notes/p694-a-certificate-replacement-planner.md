---
id: p694
title: "A certificate replacement planner"
slug: a-certificate-replacement-planner
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, TLS, Certificates, IncidentResponse, SRE]
source: "LinkedIn post P694 · IR series"
linkedin_date: 2031-03-04
design: code
script: cert_replace.py
---

# A certificate replacement planner

The certificate on the load balancer expires at noon. The same serial is also installed on two web hosts and a mail gateway. Replace it on the balancer, reload, and the other three still serve yesterday's certificate.

## Quick reference

The full script is at the end of this note: `cert_replace.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 cert_replace.py certs.json --today 2026-10-21
```

**Example output**

```text
SHARED 5C:91 on 3 hosts: lb-01, web-01, web-02
FAIL 1 shared certificate, replace as one group
```

## Explained

### What it does

`cert_replace.py` reads a certificate inventory: host, path, serial, expiry and shared_with. It sorts by expiry, prints an ORDER line per certificate, and expands shared_with so the plan names every host that must receive the same serial. It exits 1 for a shared, expired or duplicate certificate.

### What the screen shows

The fourteen lines load and sort the inventory, then print the check, the order, the shared group and the failure. The shared fixture ends on SHARED 5C:91 on 3 hosts: lb-01, web-01, web-02 and FAIL 1 shared certificate, replace as one group.

### How to run it

`python3 cert_replace.py certs.json --today 2026-10-21`. Exit 0 is a clean inventory, 1 is a finding, 2 is bad input. It never reads a private key or opens a socket.

### The fix

Replace the file on every host in the group before reloading any listener. Reload one host at a time, then verify the serial with `openssl x509 -noout -serial -in /etc/tls/site.pem`. A reload before the last copy is how one host serves a certificate the others do not have.

### Prevention

Inventory by serial, not by filename. The same path on ten hosts can hold ten different certificates.

> **The honest caveat:** the tool trusts the expiry and shared_with fields; a stale inventory produces a confident, wrong window.

> **The lesson:** a shared certificate is one change with several blast radii.

## In one line

> **Replace all, then reload.** A shared serial needs one window, not four reloads.

**Check the serial**

```bash
openssl x509 -noout -serial
```

## Script: cert_replace.py

Download: [scripts/cert_replace.py](../scripts/cert_replace.py)

```python
#!/usr/bin/env python3
"""cert_replace.py - plan a certificate replacement without breaking a peer.

Reads a certificate inventory and prints the replacement order, the hosts that
must receive the same certificate, and the serial check that proves each host
did. A certificate with shared_with is used by more than one host: every copy
must be in place before any listener reloads, or one host serves a serial the
other hosts are not serving.

Inventory (metadata only; private keys are never read):

    {"certificates": [
      {"host": "lb-01", "path": "/etc/tls/site.pem", "serial": "5C:91",
       "expiry": "2026-11-04", "shared_with": ["web-01", "web-02"]},
      {"host": "db-01", "path": "/etc/tls/db.pem", "serial": "91:02",
       "expiry": "2027-02-01", "shared_with": []}
    ]}

A shared certificate, an expired certificate and a serial listed twice are
findings. The plan is ordered by expiry, soonest first. The script prints the
plan; it does not copy a file, reload a listener or connect to a host.

Usage:
    python3 cert_replace.py certs.json
    python3 cert_replace.py certs.json --today 2026-10-21
    cat certs.json | python3 cert_replace.py -

Cron (weekly, two weeks before the first expiry):
    0 7 * * 1 python3 /opt/s0sta/cert_replace.py /etc/ir/certs.json \
      >> /var/log/ir/certs.log 2>&1

CI (fail when the inventory needs a coordinated window):
    python3 cert_replace.py /etc/ir/certs.json || exit 1

Exit codes: 0 no shared, expired or duplicate certificate, 1 at least one of
those findings, 2 usage error or unreadable, invalid or empty input.

Read-only: the inventory is opened for reading only. A certificate value or
private key in the file is ignored and never printed. The serial check is
openssl on the host; this script never runs it and never opens a socket.

By s0sta.com
"""
import argparse
import json
import sys
from datetime import date


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
    rows = document.get("certificates") if isinstance(document, dict) else document
    if not isinstance(rows, list) or not rows:
        die("expected a non-empty list under 'certificates'")
    return rows


def word(value):
    return value.strip() if isinstance(value, str) else ""


def day(value, label):
    if not isinstance(value, str) or not value.strip():
        die("%s is not an ISO date" % label)
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        die("%s is not an ISO date: %s" % (label, value))


def parse(rows):
    certs = []
    seen = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            die("certificate %d is not an object" % index)
        host = word(row.get("host"))
        path = word(row.get("path"))
        serial = word(row.get("serial"))
        if not host:
            die("certificate %d has no host" % index)
        if not path:
            die("certificate %d has no path" % index)
        if not serial:
            die("certificate %d has no serial" % index)
        if (host, path) in seen:
            die("duplicate inventory entry for %s:%s" % (host, path))
        seen.add((host, path))
        expiry = day(row.get("expiry"), "%s.expiry" % host)
        shared = row.get("shared_with")
        if shared is None:
            shared = []
        if not isinstance(shared, list):
            die("%s.shared_with must be a list" % host)
        clean = []
        for item in shared:
            name = word(item)
            if not name:
                die("%s.shared_with must contain host names" % host)
            if name == host:
                die("%s.shared_with cannot list itself" % host)
            clean.append(name)
        certs.append({"host": host, "path": path, "serial": serial,
                      "expiry": expiry, "shared": clean})
    return certs


def main():
    parser = argparse.ArgumentParser(
        description="Plan a certificate replacement in expiry order and name "
                    "every host that shares a serial.")
    parser.add_argument("inventory", nargs="?", default="-",
                        help="certificate inventory JSON; stdin when omitted")
    parser.add_argument("--today", help="ISO date to compare expiry against")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    today = day(args.today, "--today") if args.today else date.today()
    certs = parse(rows_of(load(args.inventory)))
    certs.sort(key=lambda c: (c["expiry"], c["host"], c["path"]))

    serials = {}
    for cert in certs:
        serials.setdefault(cert["serial"], []).append(cert["host"])

    for number, cert in enumerate(certs, 1):
        hosts = [cert["host"]] + cert["shared"]
        print("ORDER %d %s %s serial %s expires %s"
              % (number, cert["host"], cert["path"], cert["serial"],
                 cert["expiry"].isoformat()))
        if cert["shared"]:
            print("  REPLACE on %s before any reload" % ", ".join(hosts))
        else:
            print("  REPLACE on %s, then reload the listener" % cert["host"])
        where = "every host" if cert["shared"] else "the host"
        print("  VERIFY openssl x509 -noout -serial -in %s on %s"
              % (cert["path"], where))

    expired = [c for c in certs if c["expiry"] < today]
    for cert in expired:
        print("EXPIRED %s %s serial %s on %s"
              % (cert["host"], cert["path"], cert["serial"],
                 cert["expiry"].isoformat()))

    shared = [c for c in certs if c["shared"]]
    for cert in shared:
        hosts = [cert["host"]] + cert["shared"]
        print("SHARED %s on %d hosts: %s"
              % (cert["serial"], len(hosts), ", ".join(hosts)))

    duplicates = {serial: hosts for serial, hosts in serials.items()
                  if len(hosts) > 1}
    for serial in sorted(duplicates):
        print("FINDING serial %s listed twice: %s"
              % (serial, ", ".join(duplicates[serial])))

    if not expired and not shared and not duplicates:
        print("OK %d certificate%s, 0 shared"
              % (len(certs), "" if len(certs) == 1 else "s"))
        return 0

    reasons = []
    if expired:
        reasons.append("%d expired" % len(expired))
    if shared:
        reasons.append("%d shared certificate%s"
                       % (len(shared), "" if len(shared) == 1 else "s"))
    if duplicates:
        reasons.append("%d duplicate serial%s"
                       % (len(duplicates), "" if len(duplicates) == 1 else "s"))
    end = ", replace as one group" if shared else ""
    print("FAIL " + ", ".join(reasons) + end)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
