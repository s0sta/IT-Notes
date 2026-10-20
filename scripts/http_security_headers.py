#!/usr/bin/env python3
"""http_security_headers.py - grade the security headers of your sites.

Requests each URL and checks for the headers that protect visitors:
HSTS, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options and
Referrer-Policy. Prints a simple score per site. Great before a launch or an
audit. Standard library only.

Usage:
    python3 http_security_headers.py https://shop.example.com
    python3 http_security_headers.py -f sites.txt

By s0sta.com
"""
import argparse
import sys
import urllib.request

WANTED = [
    ("Strict-Transport-Security", "HSTS: forces HTTPS"),
    ("Content-Security-Policy", "CSP: limits what can load"),
    ("X-Content-Type-Options", "stops MIME sniffing"),
    ("X-Frame-Options", "blocks clickjacking"),
    ("Referrer-Policy", "controls the Referer header"),
]


def fetch_headers(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "s0sta-headers/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}


def main():
    ap = argparse.ArgumentParser(description="Check HTTP security headers.")
    ap.add_argument("urls", nargs="*")
    ap.add_argument("-f", "--file", help="file with one URL per line")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file) as fh:
            urls += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not urls:
        ap.error("give at least one URL, or -f a file")

    worst = 100
    for url in urls:
        try:
            headers = fetch_headers(url)
        except Exception as exc:
            print(f"[ERR ] {url} - {exc}\n")
            worst = 0
            continue
        have = [(h, d) for h, d in WANTED if h.lower() in headers]
        score = round(len(have) / len(WANTED) * 100)
        worst = min(worst, score)
        print(f"{url}  ->  {score}/100 ({len(have)}/{len(WANTED)} headers)")
        for h, d in WANTED:
            mark = "+" if h.lower() in headers else "-"
            print(f"   [{mark}] {h}  ({d})")
        print()

    sys.exit(1 if worst < 100 else 0)


if __name__ == "__main__":
    main()
