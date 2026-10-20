---
id: p217
title: "Check a site's security headers with Python"
slug: check-a-sites-security-headers-with-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, WebSecurity, DevSecOps, CyberSecurity, AppSec]
source: "LinkedIn post P217 · Cloud / DevSecOps series"
linkedin_date: 2028-02-15
design: code
script: http_security_headers.py
---

# Check a site's security headers with Python

The cheapest security win on any website is its HTTP response headers. They cost nothing to set and close whole classes of attack, yet most sites miss them. This script checks the important ones in a second. Full file attached, standard library only.

## Quick reference

The full script is at the end of this note: **http_security_headers.py** (standard library only, no `pip install`).

**Run it**

```bash
python3 http_security_headers.py https://example.com
```

**Example output**

```text
OK    Strict-Transport-Security
MISS  Content-Security-Policy
2 of 4 present
```

## Explained

### What it does

It makes one request to a URL and inspects the response headers, reporting which security headers are present and which are missing: HSTS (forces HTTPS), Content-Security-Policy (limits what scripts can load, blunting XSS), X-Content-Type-Options (stops MIME sniffing) and X-Frame-Options (prevents clickjacking). The attached version also flags a Server header that leaks version numbers and returns a non-zero exit code when something is missing, so it fits in CI.

### Why it is useful

These headers are set once in your web server or load balancer and then protect every page. A missing CSP or HSTS is a real, scannable weakness, and this is how you confirm yours are in place, before an attacker checks for you.

### How to use it

`python3 http_security_headers.py https://yoursite.com`. Run it against staging after a config change, or in a pipeline so a regression fails the build.

This is DevSecOps in miniature: a small, automatable check that turns a security best practice into something you verify every deploy instead of hoping for.

## In one line

> **Audit the headers.** Missing headers are free vulnerabilities, fixed in config.

**Check your site**

```bash
python3 http_security_headers.py https://yoursite.com
```

## Script: http_security_headers.py

Download: [scripts/http_security_headers.py](../scripts/http_security_headers.py)

```python
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
```
