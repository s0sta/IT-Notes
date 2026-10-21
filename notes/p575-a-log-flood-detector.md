---
id: p575
title: "A log flood detector"
slug: a-log-flood-detector
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, Logging, SRE, Observability]
source: "LinkedIn post P575 · PythonFixes series"
linkedin_date: 2030-05-30
design: code
script: log_flood.py
---

# A log flood detector

Between 03:12 and 03:13 the app log gains 1,600 lines, ten times the hour before. logrotate runs at 03:14, and the evidence goes with it. The incident is now a gap in the log.

## Quick reference

The full script is at the end of this note: `log_flood.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 log_flood.py /tmp/app.log
```

**Example output**

```text
FINDING 2 minutes above 200 lines/min
ALERT 03:12 900 lines, top: upstream timeout service=payments
```

## Explained

### What it does

`log_flood.py` reads a log file or stdin, takes the minute from each line in ISO, syslog or apache format, counts lines per minute and reports every minute above `--rate`. For each one it normalises the message, replacing numbers, hashes and addresses, then names the dominating pattern.

### What the screen shows

The thirteen lines read the file, define the normaliser, count the minutes, keep the ones over 200, then take the peak and its most common pattern. On the dirty fixture: FINDING 2 minutes above 200 lines/min and ALERT 03:12 900 lines, top: upstream timeout service=payments.

### How to run it

`python3 log_flood.py /var/log/app.log --rate 500`, or pipe journalctl into it. Exit 0 is no flood, 1 is a minute over the rate, 2 is unreadable input.

### The fix

The pattern names the code path. A retry loop needs a cap and jitter. One slow upstream needs a timeout shorter than the retry interval. Then delete the flood, not the log.

### Prevention

Alert on lines per minute at the source, before the disk does. journald already drops messages above its own rate limit, so a flood becomes a gap in the evidence.

> **The honest caveat:** a shared file hides which stream grew. Run it per file.

> **The lesson:** the minute is the symptom, and the repeated line is the cause.

## In one line

> **A flood hides the first error.** The minute is the symptom; the repeated line is the cause.

**Find the minute**

```bash
python3 log_flood.py /var/log/app.log
```

## Script: log_flood.py

Download: [scripts/log_flood.py](../scripts/log_flood.py)

```python
#!/usr/bin/env python3
"""log_flood.py - find the minute that flooded and the pattern behind it.

Reads a log file or stdin, buckets the lines per minute, and reports every
minute whose line count is above --rate. For each of those minutes it also
shows the dominant message pattern, with numbers, addresses and ids
normalised so that a thousand copies of one line collapse into one key.

    python3 log_flood.py /var/log/app.log --rate 200
    journalctl -u app --since "03:00" | python3 log_flood.py -
    tail -n 200000 /var/log/nginx/access.log | python3 log_flood.py - --rate 500

Timestamps are read from ISO-8601 lines, syslog/journal short lines and
apache-style `[21/Oct/2026:03:12:01` prefixes. Lines without a timestamp
are counted and reported on stderr, never bucketed.

Usage:
    python3 log_flood.py /tmp/app.log
    python3 log_flood.py /tmp/app.log --rate 50 --top 3
    python3 log_flood.py /tmp/app.log --pattern-len 40
    cat /tmp/app.log | python3 log_flood.py - --rate 120
    python3 log_flood.py --help

CI (fail a test that floods the log):
    python3 log_flood.py /tmp/test.log --rate 500 || exit 1

Cron (a five-minute check on the app log):
    */5 * * * * python3 /opt/s0sta/log_flood.py /var/log/app.log --rate 500 || exit 1

Exit codes: 0 no minute above the rate, 1 at least one minute above it,
2 usage error, unreadable input, empty input or no timestamped line.

Read-only: opens the given file, parses text and prints. It writes
nothing, changes nothing and makes no network call.

A rate is only meaningful for one source. If several applications write
to the same file, run this per file or filter first: a shared rate hides
which stream grew.

By s0sta.com
"""
import argparse
import re
import sys
from collections import Counter, defaultdict

DEFAULT_RATE = 200
DEFAULT_TOP = 5
DEFAULT_LEN = 60

# A timestamp prefix that ends just before the message. Group 1 is the
# minute key for the access-log format; ISO and syslog build it from two
# or three groups.
STAMP = (
    (re.compile(r"^(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d):\d\d"), "iso"),
    (re.compile(r"^([A-Z][a-z]{2}) +(\d{1,2}) (\d\d:\d\d):\d\d"), "syslog"),
    (re.compile(r"^\[(\d\d/[A-Za-z]{3}/\d{4}:\d\d:\d\d):\d\d(?: [^\]]*)?\]"),
     "access"),
)

UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
                  re.IGNORECASE)
IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
HASH = re.compile(r"\b(?:0x)?[0-9a-f]{12,}\b", re.IGNORECASE)
NUMBER = re.compile(r"\d+")
SPACE = re.compile(r"\s+")


class InputError(Exception):
    """An input that cannot be read."""


def read_text(source):
    """Return the whole input as text, or raise InputError."""
    try:
        if source == "-":
            text = sys.stdin.read()
        else:
            with open(source, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
    except OSError as exc:
        raise InputError("%s: %s" % (source, exc.strerror or exc))
    if not text.strip():
        raise InputError("%s: empty input" % source)
    return text


def split_line(line):
    """Return (minute_key, message) with the key None when undated."""
    for regex, kind in STAMP:
        found = regex.match(line)
        if not found:
            continue
        if kind == "iso":
            return "%s %s" % (found.group(1), found.group(2)), line[found.end():]
        if kind == "syslog":
            return ("%s %s %s" % (found.group(1), found.group(2), found.group(3)),
                    line[found.end():])
        return found.group(1), line[found.end():]
    return None, line


def pattern(message, limit):
    """Normalise a message so that copies of one line share one key."""
    text = UUID.sub("UUID", message)
    text = IP.sub("IP", text)
    text = HASH.sub("H", text)
    text = NUMBER.sub("N", text)
    text = SPACE.sub(" ", text).strip(" :-|")
    return text[:limit] or "(no message)"


def clock(key):
    """Return the short time label for a minute key."""
    return key.split(" ")[-1] if " " in key else key


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Find the minute that flooded and the pattern behind it "
                    "(read-only).")
    parser.add_argument(
        "source", nargs="?", default="-",
        help="log file to read, or - for stdin (default: -)")
    parser.add_argument(
        "--rate", type=int, default=DEFAULT_RATE, metavar="N",
        help="flag a minute with more than this many lines (default: %d)"
             % DEFAULT_RATE)
    parser.add_argument(
        "--top", type=int, default=DEFAULT_TOP, metavar="N",
        help="minutes to list (default: %d)" % DEFAULT_TOP)
    parser.add_argument(
        "--pattern-len", type=int, default=DEFAULT_LEN, metavar="N",
        help="characters kept per pattern (default: %d)" % DEFAULT_LEN)
    args = parser.parse_args(argv)

    if args.rate < 1:
        parser.error("--rate must be at least 1")
    if args.top < 1:
        parser.error("--top must be at least 1")
    if args.pattern_len < 10:
        parser.error("--pattern-len must be at least 10")

    try:
        text = read_text(args.source)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    minutes, by_minute, undated = Counter(), defaultdict(Counter), 0
    for line in text.splitlines():
        key, message = split_line(line)
        if key is None:
            undated += 1
            continue
        minutes[key] += 1
        by_minute[key][pattern(message, args.pattern_len)] += 1

    if not minutes:
        print("ERROR no timestamped line: expected ISO, syslog or "
              "[DD/Mon/YYYY:HH:MM:SS", file=sys.stderr)
        return 2
    if undated:
        print("NOTE %d line(s) have no timestamp and were not bucketed"
              % undated, file=sys.stderr)

    floods = [(key, count) for key, count in minutes.items() if count > args.rate]
    floods.sort(key=lambda item: (-item[1], item[0]))
    if not floods:
        peak = max(minutes.items(), key=lambda item: (item[1], item[0]))
        print("OK    no minute above %d lines/min, peak %s %d"
              % (args.rate, clock(peak[0]), peak[1]))
        return 0

    for key, count in floods[:args.top]:
        print("RATE  %s %d lines/min, top: %s"
              % (key, count, by_minute[key].most_common(1)[0][0]))

    peak_key, peak_count = floods[0]
    print("FINDING %d minutes above %d lines/min" % (len(floods), args.rate))
    print("ALERT %s %d lines, top: %s"
          % (clock(peak_key), peak_count, by_minute[peak_key].most_common(1)[0][0]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
