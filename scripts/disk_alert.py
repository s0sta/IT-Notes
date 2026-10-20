#!/usr/bin/env python3
"""disk_alert.py - warn before a disk fills up.

Checks the usage of one or more paths and prints an ALERT for any that
cross a threshold. Exit code is 1 if anything alerted, so it works in cron
and in monitoring. Standard library only.

Usage:
    python3 disk_alert.py                 # checks / and /var at 85%
    python3 disk_alert.py -t 90 / /data   # custom threshold and paths

Cron (every 30 min):
    */30 * * * * /usr/bin/python3 /opt/scripts/disk_alert.py >> /var/log/disk_alert.log 2>&1

By s0sta.com
"""
import argparse
import shutil
import socket
import sys


def pct_used(path):
    total, used, _free = shutil.disk_usage(path)
    return round(used / total * 100), total, used


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f}{unit}"
        n /= 1024


def main():
    ap = argparse.ArgumentParser(description="Alert when a disk crosses a usage threshold.")
    ap.add_argument("-t", "--threshold", type=int, default=85, help="percent, default 85")
    ap.add_argument("paths", nargs="*", default=["/", "/var"], help="mount points to check")
    args = ap.parse_args()

    host = socket.gethostname()
    alerted = False
    for path in args.paths:
        try:
            used, total, used_bytes = pct_used(path)
        except FileNotFoundError:
            print(f"[skip] {path} not found")
            continue
        status = "ALERT" if used >= args.threshold else "OK"
        if used >= args.threshold:
            alerted = True
        print(f"[{status}] {host}:{path} {used}% used "
              f"({human(used_bytes)} of {human(total)})")

    sys.exit(1 if alerted else 0)


if __name__ == "__main__":
    main()
