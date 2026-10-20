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
