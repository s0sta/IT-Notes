---
id: p485
title: "A DNS check in Python"
slug: a-dns-check-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [DNS, Python, DevOps, SRE, Networking]
source: "LinkedIn post P485 · Network series"
linkedin_date: 2029-11-01
design: code
script: dns_check.py
---

# A DNS check in Python

The container starts, the health check calls the API by name, and the name does not resolve. The image is fine; the resolver is not.

## Quick reference

The full script is at the end of this note: `dns_check.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 dns_check.py localhost nope.invalid
```

**Example output**

```text
  A    127.0.0.1
  AAAA ::1
```

## Explained

### What it does

The script takes a list of hostnames and calls getaddrinfo for each one with a stream socket hint. It prints every A and AAAA address it gets back, catches a failed lookup, counts rows that repeat an address, and exits 1 if any name failed.

### Why getaddrinfo

It is the same call the application makes, so it follows `/etc/hosts`, the search domains and the system resolver. dig answers a different question: what a DNS server says, not what your process will get.

It also returns addresses, not records. There is no TTL, no CNAME chain and no authority section in the result, which is why a DNS check built on it cannot tell you when the answer expires.

### Running it

Pass names on the command line or a file with `--file`. Run it after a deploy, or from cron every ten minutes; 0 means every name resolved, 1 means at least one failed, and 2 means the arguments or the file were wrong.

> **The honest caveat:** a v4-mapped IPv6 answer can look like AAAA until you check for it; the full script relabels it, the condensed version does not, and getaddrinfo has no timeout you can set, so a hung resolver hangs the check.

> **The lesson:** test the lookup your app makes, not the one dig makes.

## In one line

> **Test the lookup your app makes.** A name that fails here fails before the first byte of HTTP.

**Run it in ci**

```bash
python3 dns_check.py --file hosts.txt
```

## Script: dns_check.py

Download: [scripts/dns_check.py](../scripts/dns_check.py)

```python
#!/usr/bin/env python3
"""dns_check.py - resolve hostnames and fail when one does not resolve.

Every hostname is resolved with socket.getaddrinfo, the same call an
application makes. The script prints each IPv4 and IPv6 address it gets back,
reports a name that fails, and counts addresses that arrive more than once.
It exits 1 when any name fails, so a pipeline can stop before the app does.

getaddrinfo is not a DNS client. It follows the system name service switch
(usually /etc/hosts, DNS and mDNS), applies search domains and returns
addresses rather than records: no TTL, no CNAME chain, no authority section.
That is the point. It answers what the process will actually get.

Usage:
    python3 dns_check.py example.com
    python3 dns_check.py example.com api.example.com
    python3 dns_check.py --file hosts.txt
    python3 dns_check.py --file hosts.txt example.com
    python3 dns_check.py --help

A host file has one name per line; blank lines and lines starting with # are
ignored.

CI (after a deploy, with the names the service needs):
    python3 dns_check.py --file /etc/s0sta/hosts.txt || exit 1

Cron (every ten minutes):
    */10 * * * * python3 /opt/s0sta/dns_check.py --file /etc/s0sta/hosts.txt

Exit codes: 0 every name resolved, 1 at least one name failed, 2 usage or
input error.
Read-only: no file is written and no connection is opened; the only traffic
is the resolver lookups that getaddrinfo makes.

By s0sta.com
"""
import argparse
import ipaddress
import socket
import sys


def read_hosts(path):
    """Return the hostnames in one file, or raise ValueError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as exc:
        raise ValueError("cannot read %s: %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError as exc:
        raise ValueError("%s is not UTF-8 text: %s" % (path, exc.reason))
    hosts = []
    for number, line in enumerate(lines, 1):
        name = line.split("#", 1)[0].strip()
        if not name:
            continue
        if any(ch.isspace() for ch in name):
            raise ValueError("%s line %d: a hostname cannot contain spaces"
                             % (path, number))
        hosts.append(name)
    return hosts


def clean(host):
    """Validate one command-line hostname and return it."""
    name = host.strip()
    if not name:
        raise ValueError("empty hostname")
    if any(ch.isspace() for ch in name):
        raise ValueError("hostname %r contains a space" % host)
    return name


def classify(address):
    """Return (tag, shown, note) for one getaddrinfo address."""
    bare = address.split("%", 1)[0]
    try:
        ip = ipaddress.ip_address(bare)
    except ValueError:
        return "?", address, ""
    if ip.version == 6 and ip.ipv4_mapped is not None:
        return "A", str(ip.ipv4_mapped), "v4-mapped"
    if ip.version == 6:
        return "AAAA", address, ""
    return "A", address, ""


def dedupe(rows):
    """Return (unique rows, duplicate rows), keeping the first of each."""
    seen = set()
    unique = []
    duplicates = []
    for row in rows:
        key = (row[0], row[1])
        if key in seen:
            duplicates.append(row)
            continue
        seen.add(key)
        unique.append(row)
    return unique, duplicates


def resolve(host):
    """Resolve one name; return (unique rows, duplicate rows)."""
    infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC,
                               socket.SOCK_STREAM)
    rows = [classify(info[4][0]) for info in infos]
    return dedupe(rows)


def build_parser():
    """Return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="dns_check.py",
        description="Resolve hostnames with socket.getaddrinfo, print each "
                    "A and AAAA address, and exit 1 when a name fails. "
                    "This tests the lookup the application will make, not "
                    "what a public DNS resolver would answer.")
    parser.add_argument("hosts", nargs="*", metavar="HOST",
                        help="hostname to resolve; repeat for more")
    parser.add_argument("--file", action="append", default=[], metavar="PATH",
                        help="read hostnames from a file, one per line; "
                             "can be given more than once")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.hosts and not args.file:
        parser.error("give at least one HOST or --file PATH")

    hosts = []
    try:
        for host in args.hosts:
            hosts.append(clean(host))
        for path in args.file:
            hosts.extend(read_hosts(path))
    except ValueError as exc:
        parser.error(str(exc))
    if not hosts:
        parser.error("no hostnames found")

    failed = 0
    addresses = 0
    duplicates = 0
    for host in hosts:
        try:
            rows, dups = resolve(host)
        except (socket.gaierror, UnicodeError, OSError) as exc:
            reason = getattr(exc, "strerror", None) or str(exc)
            print("FAIL  %-28s %s" % (host, reason))
            failed += 1
            continue
        if not rows:
            print("FAIL  %-28s no addresses returned" % host)
            failed += 1
            continue
        addresses += len(rows)
        duplicates += len(dups)
        for tag, addr, note in rows:
            extra = "  (%s)" % note if note else ""
            print("%-5s %-28s %s%s" % (tag, host, addr, extra))
        for tag, addr, _note in dups:
            print("%-5s %-28s %s  (duplicate)" % ("DUP", host, addr))

    print("%d/%d hosts resolved, %d addresses, %d duplicate, %d failed"
          % (len(hosts) - failed, len(hosts), addresses, duplicates, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```
