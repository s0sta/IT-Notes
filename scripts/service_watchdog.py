#!/usr/bin/env python3
"""service_watchdog.py - restart a dead systemd service, and log it.

Checks each systemd service with `systemctl is-active`. If one is down, it
tries to restart it and records what happened. Run it from cron as a safety
net between proper monitoring checks. Standard library only (uses systemctl).

Usage:
    python3 service_watchdog.py nginx php8.3-fpm mariadb
    sudo python3 service_watchdog.py --restart nginx     # actually restart

Without --restart it only reports (safe dry run). Needs root to restart.

By s0sta.com
"""
import argparse
import datetime as dt
import subprocess
import sys


def is_active(service):
    r = subprocess.run(["systemctl", "is-active", service],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def restart(service):
    r = subprocess.run(["systemctl", "restart", service],
                       capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def main():
    ap = argparse.ArgumentParser(description="Watch systemd services and restart if down.")
    ap.add_argument("services", nargs="+")
    ap.add_argument("--restart", action="store_true", help="actually restart (default: report only)")
    args = ap.parse_args()

    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    problems = False
    for svc in args.services:
        if is_active(svc):
            print(f"{now} [OK] {svc} active")
            continue
        problems = True
        if not args.restart:
            print(f"{now} [DOWN] {svc} is not active (dry run, use --restart)")
            continue
        ok, err = restart(svc)
        if ok and is_active(svc):
            print(f"{now} [FIXED] {svc} was down, restarted successfully")
        else:
            print(f"{now} [FAIL] {svc} down, restart failed: {err}")

    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
