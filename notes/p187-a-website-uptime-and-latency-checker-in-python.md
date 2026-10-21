---
id: p187
title: "A website uptime and latency checker in Python"
slug: a-website-uptime-and-latency-checker-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, DevOps, Monitoring, SRE, Automation]
source: "LinkedIn post P187 · Cloud / DevSecOps series"
linkedin_date: 2027-12-07
design: code
script: url_uptime.py
---

# A website uptime and latency checker in Python

Monitoring runs through the whole plan, from Linux to Kubernetes, so here is a tiny uptime checker you can run anywhere Python exists. It requests each URL, reports the status code and response time, and alerts on failures or slow responses. Full file attached, no dependencies.

## Quick reference

The full script is at the end of this note: `url_uptime.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 url_uptime.py https://shop.example.com
```

**Example output**

```text
[OK] https://shop.example.com 200 in 182 ms
```

## Explained

### What it does

For each URL it records the HTTP status and how long the request took. If the status is an error, or the response is slower than your threshold, it flags it and exits 1, so cron or a pipeline treats it as a failure.

### Why this beats a simple ping

ping only tells you a server answers ICMP. It says nothing about whether the website actually works. This checks the real endpoint, the page or health route users hit, so a 500 error or a 5-second page both show up.

### How to use it

Keep your URLs in a file and run it every few minutes: `*/5 * * * * python3 url_uptime.py -s 2.0 -f urls.txt`. Point it at a real health endpoint, not just the homepage, so it exercises the app and not just the web server.

The attached version adds a slow threshold, reads URLs from a file, sets a sane User-Agent, and handles timeouts and connection errors cleanly instead of crashing on the first one.

It is not a replacement for a full monitoring stack, but it is a dependency-free check you can drop on any box in two minutes, and it has caught real outages for me before a customer noticed.

## In one line

> **Check the thing users actually use.** Ping the real page, not just the server.

**Watch your sites**

```bash
*/5 * * * * python3 url_uptime.py -f urls.txt
```

## Script: url_uptime.py

Download: [scripts/url_uptime.py](../scripts/url_uptime.py)

```python
#!/usr/bin/env python3
"""url_uptime.py - check that your sites and APIs are up and fast.

Requests each URL, reports the status code and response time, and alerts
(exit 1) on any failure or slow response. No dependencies, so it runs on any
server with Python. Good as a cron check or a simple status page feeder.

Usage:
    python3 url_uptime.py https://shop.example.com https://api.example.com/health
    python3 url_uptime.py -s 2.0 -f urls.txt

-s is the slow threshold in seconds.

By s0sta.com
"""
import argparse
import sys
import time
import urllib.request


def check(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "s0sta-uptime/1.0"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resp.read(1)  # touch the body
        code = resp.status
    return code, time.perf_counter() - start


def main():
    ap = argparse.ArgumentParser(description="Check URL uptime and latency.")
    ap.add_argument("urls", nargs="*")
    ap.add_argument("-s", "--slow", type=float, default=2.0, help="slow threshold seconds")
    ap.add_argument("-f", "--file", help="file with one URL per line")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file) as fh:
            urls += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not urls:
        ap.error("give at least one URL, or -f a file")

    bad = False
    for url in urls:
        try:
            code, secs = check(url)
        except Exception as exc:
            print(f"[DOWN] {url} - {exc}")
            bad = True
            continue
        slow = secs > args.slow
        tag = "OK" if 200 <= code < 400 and not slow else ("SLOW" if slow else "WARN")
        if tag != "OK":
            bad = True
        print(f"[{tag}] {url} {code} in {secs * 1000:.0f} ms")

    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
```
