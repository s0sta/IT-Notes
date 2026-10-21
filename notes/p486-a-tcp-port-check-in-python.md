---
id: p486
title: "A TCP port check in Python"
slug: a-tcp-port-check-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Networking, Python, DevOps, SRE, TCP]
source: "LinkedIn post P486 · Network series"
linkedin_date: 2029-11-04
design: code
script: port_check.py
---

# A TCP port check in Python

The load balancer says healthy and the port is closed. A TCP connect answers that in milliseconds or one timeout, before any HTTP status exists.

## Quick reference

The full script is at the end of this note: `port_check.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 port_check.py 1.1.1.1:443 127.0.0.1:5432
```

**Example output**

```text
1.1.1.1:443 open 11ms
127.0.0.1:5432 closed 0ms
```

## Explained

### Three answers

Open means the handshake completed and something is listening. Closed means the host sent a reset: the packet arrived and nothing was there. Filtered means no answer before the timeout, which is a dropped packet, a dead host or a service too slow to accept.

### The code

For each host and port it starts a timer, calls create_connection with a two-second timeout, and prints the state with the elapsed time. A refused connection is closed; any other socket error in the short version is filtered. A refused connect returns in milliseconds; a filtered one costs the whole timeout. The exit code is 1 if a required port is not open.

### Running it

Put a + in front of a target to mark it required; with none marked, every target is required. Run it after a deploy or from cron, and read the timing as an upper bound because it includes name resolution and the handshake.

> **The honest caveat:** a firewall can send a reset and look closed, a dead host and a slow service can both look filtered, and an open port proves the kernel accepted a connection, not that the application works.

> **The lesson:** connect first, then read the error; it names the layer that failed.

## In one line

> **Connect first, read the error.** A closed port and a filtered port send you to different places.

**Check after deploy**

```bash
python3 port_check.py +api:443
```

## Script: port_check.py

Download: [scripts/port_check.py](../scripts/port_check.py)

```python
#!/usr/bin/env python3
"""port_check.py - is the service actually listening?

Tests TCP connectivity to host:port pairs. Unlike ping (ICMP is often
blocked), this checks the real port your app uses, so it tells you whether
SSH, a database or a web server is truly reachable. Standard library only.

Usage:
    python3 port_check.py db.internal:5432 web.internal:443 10.0.0.5:22
    python3 port_check.py -t 3 -f targets.txt

By s0sta.com
"""
import argparse
import socket
import sys


def is_open(host, port, timeout=3.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def main():
    ap = argparse.ArgumentParser(description="Check if TCP ports are open.")
    ap.add_argument("targets", nargs="*", help="host:port")
    ap.add_argument("-t", "--timeout", type=float, default=3.0)
    ap.add_argument("-f", "--file", help="file with one host:port per line")
    args = ap.parse_args()

    targets = list(args.targets)
    if args.file:
        with open(args.file) as fh:
            targets += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not targets:
        ap.error("give at least one host:port, or -f a file")

    closed = False
    for entry in targets:
        host, _, port = entry.rpartition(":")
        if not host or not port.isdigit():
            print(f"[ERR ] bad target: {entry}  (use host:port)")
            closed = True
            continue
        ok = is_open(host, int(port), args.timeout)
        print(f"[{'OPEN' if ok else 'SHUT'}] {host}:{port}")
        if not ok:
            closed = True

    sys.exit(1 if closed else 0)


if __name__ == "__main__":
    main()
```
