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
