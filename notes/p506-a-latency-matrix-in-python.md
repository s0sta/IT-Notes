---
id: p506
title: "A latency matrix in Python"
slug: a-latency-matrix-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Networking, SRE, DevOps, Performance]
source: "LinkedIn post P506 · Network series"
linkedin_date: 2029-12-20
design: code
script: latency_matrix.py
---

# A latency matrix in Python

A dashboard says the API is slow, and the p99 is fine. The problem is one target that takes 300 ms to accept a TCP connection, and nobody measured the connect step on its own.

## Quick reference

The full script is at the end of this note: `latency_matrix.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 latency_matrix.py db:5432 api:443 5 250
```

**Example output**

```text
db:5432 p50=0.4 p95=0.9
api:443 p50=1.2 p95=18.4
```

## Explained

### What it measures

The script takes a list of host:port targets, opens a TCP connection to each one, closes it, and times the handshake. It repeats that N times, five by default, then reports p50 and p95 per target in milliseconds. No HTTP request, no TLS, no payload: this is the network and the listen backlog, before the application says anything.

### The verdict

Each target's p95 is compared with a budget, 250 ms by default. The script exits 1 when one is over, or when a connection fails, and 0 when every target is inside it. The attached version also prints the failure count and names the slowest target, so a red build tells you where to look.

### How to use it

Run `python3 latency_matrix.py db:5432 api:443` from the same network segment as the caller. A laptop on VPN measures the VPN, not the cluster. Put it in a cron or a synthetic check, and keep a baseline for each target so a p95 of 40 ms is read against its own history, not against another service.

> **The honest caveat:** a TCP connect measures reachability and backlog, not application latency. A fast handshake with a slow response is a different problem, so pair this with an HTTP check.

> **The lesson:** measure the layer you blame.

## In one line

> **A fast connect is not a fast reply.** Measure the layer you blame, not the one you know.

**Measure the connect**

```bash
python3 latency_matrix.py db:5432 --repeat 5
```

## Script: latency_matrix.py

Download: [scripts/latency_matrix.py](../scripts/latency_matrix.py)

```python
#!/usr/bin/env python3
"""Measure TCP connect latency to a list of hosts and enforce a budget.

Usage:
    python3 latency_matrix.py db:5432 api:443
    python3 latency_matrix.py db:5432 api:443 --repeat 10 --budget 150
    python3 latency_matrix.py db:5432 --timeout 1

Each target is HOST:PORT. The tool opens a TCP connection, closes it, and
times the handshake. It repeats --repeat times (default 5), prints p50 and
p95 in milliseconds per target, names the slowest target, and exits 1 when
a p95 is over --budget (default 250 ms) or a connection fails.

Exit codes: 0 clean, 1 finding, 2 usage or input error.
Read-only: it connects and closes; it sends no application data.
Cron: */5 * * * * python3 latency_matrix.py db:5432 api:443 >> /var/log/latency.log
CI:   python3 latency_matrix.py db:5432 api:443 || exit 1
By s0sta.com
"""

import argparse
import socket
import sys
import time


def positive_int(text):
    """argparse type for a whole number of 1 or more."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a whole number")
    if value < 1:
        raise argparse.ArgumentTypeError("expected a number of 1 or more")
    return value


def positive_float(text):
    """argparse type for a number greater than zero."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a number")
    if value <= 0:
        raise argparse.ArgumentTypeError("expected a number greater than zero")
    return value


def target(text):
    """argparse type for HOST:PORT, returning (host, port, original)."""
    host, separator, port_text = text.rpartition(":")
    if not separator or not host or not port_text.isdigit():
        raise argparse.ArgumentTypeError(f"expected HOST:PORT, got {text!r}")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"port out of range in {text!r}")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    return host, port, text


def measure(host, port, timeout, repeat):
    """Return (successful connect times in ms, number of failed attempts)."""
    samples = []
    failures = 0
    for _ in range(repeat):
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                samples.append((time.perf_counter() - start) * 1000)
        except OSError:
            failures += 1
    return samples, failures


def percentile(values, fraction):
    """Linear-interpolated percentile of a non-empty list."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Time TCP connects to HOST:PORT targets and fail over a p95 budget.")
    parser.add_argument("targets", nargs="+", type=target, metavar="HOST:PORT",
                        help="targets to measure, for example db:5432 api:443")
    parser.add_argument("--repeat", type=positive_int, default=5, metavar="N",
                        help="connects per target (default: 5)")
    parser.add_argument("--budget", type=positive_float, default=250.0, metavar="MS",
                        help="p95 budget per target in milliseconds (default: 250)")
    parser.add_argument("--timeout", type=positive_float, default=2.0, metavar="S",
                        help="connect timeout per attempt in seconds (default: 2)")
    args = parser.parse_args(argv)

    rows = []
    for host, port, label in args.targets:
        samples, failures = measure(host, port, args.timeout, args.repeat)
        if samples:
            p50 = percentile(samples, 0.50)
            p95 = percentile(samples, 0.95)
        else:
            p50 = p95 = float("nan")
        rows.append((label, samples, failures, p50, p95))

    print(f"{'TARGET':<26}{'N':>3}{'FAIL':>6}{'P50':>9}{'P95':>9}")
    for label, samples, failures, p50, p95 in rows:
        if samples:
            print(f"{label:<26}{len(samples):>3}{failures:>6}"
                  f"{p50:>7.1f}ms{p95:>7.1f}ms")
        else:
            print(f"{label:<26}{0:>3}{failures:>6}{'FAIL':>9}{'FAIL':>9}")

    findings = []
    for label, samples, failures, p50, p95 in rows:
        if failures:
            findings.append(f"{label}: {failures}/{args.repeat} connections failed")
        if samples and p95 > args.budget:
            findings.append(f"{label}: p95 {p95:.1f} ms over budget {args.budget:g} ms")

    reachable = [row for row in rows if row[1]]
    if reachable:
        slowest = max(reachable, key=lambda row: row[4])
        print(f"SLOWEST {slowest[0]} p95 {slowest[4]:.1f} ms")

    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print(f"OK every p95 under {args.budget:g} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
