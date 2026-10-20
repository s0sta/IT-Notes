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
