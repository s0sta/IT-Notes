---
id: p212
title: "Find SSH brute-force attempts with Python"
slug: find-ssh-brute-force-attempts-with-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, CyberSecurity, Linux, BlueTeam, DevSecOps]
source: "LinkedIn post P212 · Cloud / DevSecOps series"
linkedin_date: 2028-02-03
design: code
script: ssh_failed_logins.py
---

# Find SSH brute-force attempts with Python

Security phase of the plan. Your SSH log is full of brute-force noise; the useful question is who, and how much. This script parses an auth log and prints the top source IPs and the usernames they tried. Full file attached, standard library only.

## Quick reference

The full script is at the end of this note: **ssh_failed_logins.py** (standard library only, no `pip install`).

**Run it**

```bash
python3 ssh_failed_logins.py /var/log/auth.log
```

**Example output**

```text
  4821  203.0.113.42
   912  198.51.100.7
  2 unique IPs, 5733 attempts
```

## Explained

### What it does

It reads the auth log line by line, matches the "Failed password ... from IP" pattern with a regex, and counts attempts per IP and per username. The output is a short, ranked list: the IPs hammering you most, and whether they are guessing root, admin or real usernames.

### Why it is useful

A raw log is thousands of lines no one reads. This turns it into a decision: the top IPs go into a firewall drop rule or a fail2ban jail, and seeing attempts on a real username tells you that account name has leaked.

### How to use it

`python3 ssh_failed_logins.py /var/log/auth.log`, or pipe journalctl into it: `journalctl -u ssh | python3 ssh_failed_logins.py` -. On RHEL the log is `/var/log/secure`.

The attached version reads from a file or stdin, shows totals and unique IP counts, and lets you choose how many to display.

The deeper lesson, straight from the security path: the best fix is to make brute force pointless. Disable password authentication and use SSH keys, and these thousands of attempts become thousands of harmless failures. This script is how you see the threat and confirm your defences are working.

## In one line

> **Make the log tell you who.** The top IPs are your firewall or fail2ban list.

**Run it on a server**

```bash
python3 ssh_failed_logins.py /var/log/auth.log
```

## Script: ssh_failed_logins.py

Download: [scripts/ssh_failed_logins.py](../scripts/ssh_failed_logins.py)

```python
#!/usr/bin/env python3
"""ssh_failed_logins.py - who is trying to brute-force your SSH?

Parses an auth log for failed SSH logins and prints the top source IPs and
the usernames they tried. Turns a noisy log into a short list you can act on
(firewall, fail2ban, or just awareness). Standard library only.

Usage:
    python3 ssh_failed_logins.py /var/log/auth.log
    python3 ssh_failed_logins.py -n 20 /var/log/auth.log
    journalctl -u ssh | python3 ssh_failed_logins.py -   # read from stdin

By s0sta.com
"""
import argparse
import re
import sys
from collections import Counter

FAIL = re.compile(r"Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)")


def parse(lines):
    ips, users = Counter(), Counter()
    for line in lines:
        m = FAIL.search(line)
        if m:
            users[m.group(1)] += 1
            ips[m.group(2)] += 1
    return ips, users


def main():
    ap = argparse.ArgumentParser(description="Summarise failed SSH logins.")
    ap.add_argument("logfile", help="path to auth log, or - for stdin")
    ap.add_argument("-n", "--top", type=int, default=10, help="how many to show")
    args = ap.parse_args()

    src = sys.stdin if args.logfile == "-" else open(args.logfile, errors="ignore")
    ips, users = parse(src)
    if src is not sys.stdin:
        src.close()

    total = sum(ips.values())
    print(f"{total} failed SSH attempts from {len(ips)} unique IPs\n")
    print(f"Top {args.top} source IPs:")
    for ip, n in ips.most_common(args.top):
        print(f"  {n:>6}  {ip}")
    print(f"\nTop {args.top} usernames tried:")
    for user, n in users.most_common(args.top):
        print(f"  {n:>6}  {user}")


if __name__ == "__main__":
    main()
```
