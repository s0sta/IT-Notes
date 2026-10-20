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
