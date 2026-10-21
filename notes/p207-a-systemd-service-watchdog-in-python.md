---
id: p207
title: "A systemd service watchdog in Python"
slug: a-systemd-service-watchdog-in-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, SysAdmin, DevOps, Automation]
source: "LinkedIn post P207 · Cloud / DevSecOps series"
linkedin_date: 2028-01-23
design: code
script: service_watchdog.py
---

# A systemd service watchdog in Python

Sometimes a service dies between monitoring checks, and you want it back before anyone notices. This script checks systemd services and, if one is down, restarts it and records what happened. Full file attached, standard library only (it drives systemctl).

## Quick reference

The full script is at the end of this note: `service_watchdog.py` (standard library only, no `pip install`).

**Run it**

```bash
sudo python3 service_watchdog.py --restart nginx
```

**Example output**

```text
[OK] nginx active
[FIXED] php8.3-fpm was down, restarted
```

## Explained

### What it does

For each service you name, it runs systemctl is-active. If the service is up, it logs OK. If it is down and you passed `--restart`, it restarts it and logs FIXED or, if the restart fails, FAIL with the reason. Every line is timestamped, so the log is an honest record of what went down and when.

### The safe default

Without `--restart` it only reports. That is deliberate: run it in dry mode first to see what it would do, then add `--restart` once you trust it. Restarting services needs root, so it runs under sudo or as a root cron job.

### How to use it

`*/5 * * * * /usr/bin/python3 /opt/scripts/service_watchdog.py --restart nginx php8.3-fpm` mariadb >> `/var/log/watchdog.log 2>&1`. Every five minutes it makes sure your key services are alive.

> **An honest caveat:** this is a backstop, not real monitoring. If a service keeps dying, auto-restarting it hides the real problem. The log is there so you notice the pattern. systemd itself can also do this with Restart=on-failure in the unit; this script is handy when you want one scheduled check across several services with a single log.

## In one line

> **A safety net between checks.** Not a replacement for monitoring, but a cheap backstop.

**Run it often**

```bash
*/5 * * * * python3 service_watchdog.py --restart nginx
```

## Script: service_watchdog.py

Download: [scripts/service_watchdog.py](../scripts/service_watchdog.py)

```python
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
```
