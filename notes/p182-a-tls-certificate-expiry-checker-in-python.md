---
id: p182
title: "A TLS certificate expiry checker in Python"
slug: a-tls-certificate-expiry-checker-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, TLS, CyberSecurity, DevOps, Monitoring]
source: "LinkedIn post P182 · Cloud / DevSecOps series"
linkedin_date: 2027-11-25
design: code
script: ssl_expiry_check.py
---

# A TLS certificate expiry checker in Python

Azure phase of the plan means running web apps and APIs, and the fastest way to take one down is an expired TLS certificate. This script checks expiry for any list of domains and alerts before it is too late. Full file attached, standard library only.

## Quick reference

The full script is at the end of this note: **ssl_expiry_check.py** (standard library only, no `pip install`).

**Run it**

```bash
python3 ssl_expiry_check.py -w 14 shop.example.com
```

**Example output**

```text
[ALERT] shop.example.com:443 expires in 9 days
```

## Explained

### What it does

It connects to each host, reads the certificate the server actually presents, and works out how many days are left. If any cert is inside your warning window, it prints an ALERT and exits 1, so cron or a pipeline can act on it.

### Why read the live cert

Checking the real certificate the server serves catches problems a file on disk cannot: the wrong cert deployed, a missing intermediate, or a renewal that happened but was never reloaded. You test what the world sees.

### How to use it

Put your domains in a file and run it daily: `0 8 * * * python3 ssl_expiry_check.py -w 14 -f domains.txt`. Fourteen days of warning is plenty of time for even a manual renewal, and far better than an alert from an angry customer.

The attached version takes a warning window, reads domains from a file, supports host:port, and handles unreachable hosts gracefully instead of crashing.

Even with auto-renewal like Let's Encrypt or Azure-managed certs, keep this running. Renewals fail quietly: port 80 closed, DNS moved, a reload that never happened. This is the backstop that catches it.

## In one line

> **Watch expiry like a hawk.** An expired cert is a full outage that a cron job prevents.

**Daily check**

```bash
0 8 * * * python3 ssl_expiry_check.py -f domains.txt
```

## Script: ssl_expiry_check.py

Download: [scripts/ssl_expiry_check.py](../scripts/ssl_expiry_check.py)

```python
#!/usr/bin/env python3
"""ssl_expiry_check.py - warn before a TLS certificate expires.

Connects to each host, reads the certificate, and prints how many days are
left. Alerts (exit 1) if any cert expires within the warning window. Great
for a daily cron so a renewal never surprises you. Standard library only.

Usage:
    python3 ssl_expiry_check.py example.com shop.example.com
    python3 ssl_expiry_check.py -w 21 -f domains.txt

domains.txt: one host (or host:port) per line.

By s0sta.com
"""
import argparse
import datetime as dt
import socket
import ssl
import sys


def days_left(host, port=443, timeout=5):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    expires = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
    return (expires - dt.datetime.utcnow()).days, expires.date()


def main():
    ap = argparse.ArgumentParser(description="Check TLS certificate expiry.")
    ap.add_argument("hosts", nargs="*", help="host or host:port")
    ap.add_argument("-w", "--warn", type=int, default=14, help="warn if days left <= this")
    ap.add_argument("-f", "--file", help="file with one host per line")
    args = ap.parse_args()

    hosts = list(args.hosts)
    if args.file:
        with open(args.file) as fh:
            hosts += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not hosts:
        ap.error("give at least one host, or -f a file")

    alerted = False
    for entry in hosts:
        host, _, port = entry.partition(":")
        port = int(port) if port else 443
        try:
            left, when = days_left(host, port)
        except Exception as exc:
            print(f"[ERR ] {host}:{port} - {exc}")
            alerted = True
            continue
        tag = "ALERT" if left <= args.warn else "OK"
        if left <= args.warn:
            alerted = True
        print(f"[{tag}] {host}:{port} expires in {left} days ({when})")

    sys.exit(1 if alerted else 0)


if __name__ == "__main__":
    main()
```
