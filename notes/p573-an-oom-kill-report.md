---
id: p573
title: "An OOM kill report"
slug: an-oom-kill-report
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, SRE, Kernel, Troubleshooting]
source: "LinkedIn post P573 · PythonFixes series"
linkedin_date: 2030-05-26
design: code
script: oom_report.py
---

# An OOM kill report

At 03:04 the API goes quiet and comes back at 03:06 with no deploy and no traceback. The kernel killed the process, and the only witness is a few hundred lines of dmesg that nobody reads until morning.

## Quick reference

The full script is at the end of this note: `oom_report.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 oom_report.py /tmp/dmesg.txt
```

**Example output**

```text
FINDING 3 OOM kills
ALERT python3 pid 4242, 3082MB, adj 0
```

## Explained

### What it does

`oom_report.py` reads dmesg or journal text, finds every Out of memory: Killed process line and pulls the pid, the process name, anon-rss and oom_score_adj out of it. Older kernels print score N on the line before, so that score is attached to the same pid. Victims are ranked by resident memory.

### What the screen shows

The fourteen lines compile one regex, loop over the file, convert kB to MB, sort by RSS, print the count and name the worst victim. On the dirty fixture: FINDING 3 OOM kills and ALERT python3 pid 4242, 3082MB, adj 0.

### How to run it

`journalctl -k --since 03:00 | python3 oom_report.py` - `--since 1h`, or point it at a saved dmesg. Exit 0 is no kill, 1 is at least one, 2 is unreadable input.

### The fix

The victim is rarely the problem. Check its resident memory a day earlier, then cap the unit with MemoryMax=2G, so the cgroup kills one service, not the whole box.

### Prevention

Alert on the oom_kill counter, not on the restart. A service killed twice in a week is a leak with a schedule.

> **The honest caveat:** modern kernels log oom_score_adj, the adjustment, not the oom_score they computed.

> **The lesson:** the kernel does not kill the biggest process, it kills the one with the worst score.

## In one line

> **The kernel kept the receipts.** dmesg remembers the victim, the pid and the score.

**Read the kills**

```bash
journalctl -k | grep -i oom
```

## Script: oom_report.py

Download: [scripts/oom_report.py](../scripts/oom_report.py)

```python
#!/usr/bin/env python3
"""oom_report.py - rank the victims of OOM kills from dmesg or journal text.

Reads kernel log text (a file or stdin), finds every
`Out of memory: Killed process` line, and ranks the victims by resident
memory, with the kernel's oom_score_adj and, when the log has it, the
`score N` that older kernels print.

    journalctl -k --since "03:00" > /tmp/kernel.txt
    python3 oom_report.py /tmp/kernel.txt
    dmesg -T | python3 oom_report.py

The report prints a table (pid, RSS in MB, adjust, score, process, time)
and two summary lines. Exit 1 when at least one kill is in the window.

--since accepts a duration (90m, 24h, 7d) or an ISO instant
(2026-10-21T03:00:00). Lines with no timestamp cannot be filtered: they
are kept and counted in a note on stderr. `dmesg` without -T has only
uptime, so use `dmesg -T` or journalctl -k when you need the window.

Usage:
    python3 oom_report.py /tmp/kernel.txt
    python3 oom_report.py /tmp/kernel.txt --since 24h --top 3
    journalctl -k --since "today" | python3 oom_report.py - --since 24h
    python3 oom_report.py --help

CI (fail a soak test that triggered the OOM killer):
    python3 oom_report.py /var/log/kern.log --since 2h || exit 1

Cron (a daily kill report on the on-call channel):
    0 7 * * * journalctl -k --since yesterday | python3 /opt/s0sta/oom_report.py - --since 24h

Exit codes: 0 no kill in the window, 1 at least one kill in the window,
2 usage error or unreadable, empty input.

Read-only: opens the given file, parses text and prints. It writes
nothing, changes nothing and makes no network call.

The kernel logs oom_score_adj, not the oom_score it computed, so on a
modern host the adjust column is what you get and RSS decides the order.
Older kernels print `Kill process <pid> (... ) score N`, and that score
is shown when the line is present.

By s0sta.com
"""
import argparse
import re
import sys
from datetime import datetime, timedelta

DEFAULT_TOP = 5

KILL = re.compile(r"Killed process (\d+)(?: \(([^)]*)\))?")
DECISION = re.compile(r"Kill process (\d+) \([^)]*\) score (\d+)")
RSS = re.compile(r"anon-rss:(\d+)kB")
ADJ = re.compile(r"oom_score_adj:(-?\d+)")

STAMP = (
    # dmesg -T: [Tue Oct 21 03:12:01 2026]
    (re.compile(r"\[[A-Z][a-z]{2} ([A-Z][a-z]{2} +\d{1,2} \d\d:\d\d:\d\d \d{4})\]"),
     "%b %d %H:%M:%S %Y"),
    # journalctl -o short-iso: 2026-10-21T03:12:01+0000
    (re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:[.,]\d+)?(?:Z|[+-]\d\d:?\d\d)?)"),
     "iso"),
    # app log or journal short-iso with a space
    (re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)"), "iso"),
    # journalctl short: Oct 21 03:12:01
    (re.compile(r"^([A-Z][a-z]{2} +\d{1,2} \d\d:\d\d:\d\d)"), "syslog"),
)


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


def parse_stamp(line):
    """Return a naive local datetime for the line, or None."""
    for regex, kind in STAMP:
        found = regex.search(line)
        if not found:
            continue
        token = found.group(1)
        try:
            if kind == "iso":
                value = datetime.fromisoformat(token.replace(",", "."))
                if value.tzinfo is not None:
                    value = value.astimezone().replace(tzinfo=None)
                return value
            if kind == "%b %d %H:%M:%S %Y":
                return datetime.strptime(token, kind)
            value = datetime.strptime(token, "%b %d %H:%M:%S")
            value = value.replace(year=datetime.now().year)
            if value - datetime.now() > timedelta(days=1):
                value = value.replace(year=value.year - 1)
            return value
        except ValueError:
            return None
    return None


def parse_window(text):
    """Return the cutoff datetime for --since, or raise InputError."""
    found = re.fullmatch(r"(\d+)([smhd])", text.strip())
    if found:
        unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}[found.group(2)]
        return datetime.now() - timedelta(seconds=int(found.group(1)) * unit)
    try:
        value = datetime.fromisoformat(text.strip())
    except ValueError:
        raise InputError("--since needs 90m, 24h, 7d or an ISO datetime")
    if value.tzinfo is not None:
        value = value.astimezone().replace(tzinfo=None)
    return value


def parse(text):
    """Return (victims, undated, unreadable) from kernel log text."""
    victims, scores, undated, unreadable = [], {}, 0, 0
    for raw in text.splitlines():
        decision = DECISION.search(raw)
        if decision:
            scores[int(decision.group(1))] = int(decision.group(2))
            continue
        found = KILL.search(raw)
        if not found:
            continue
        pid = int(found.group(1))
        comm = (found.group(2) or "?").strip() or "?"
        rss = RSS.search(raw)
        adj = ADJ.search(raw)
        if rss is None:
            unreadable += 1
        stamp = parse_stamp(raw)
        if stamp is None:
            undated += 1
        victims.append({
            "pid": pid,
            "comm": comm,
            "rss_kb": int(rss.group(1)) if rss else 0,
            "adj": int(adj.group(1)) if adj else None,
            "score": scores.get(pid),
            "stamp": stamp,
        })
    return victims, undated, unreadable


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank the victims of OOM kills from kernel log text "
                    "(read-only).")
    parser.add_argument(
        "source", nargs="?", default="-",
        help="dmesg or journal text to read, or - for stdin (default: -)")
    parser.add_argument(
        "--since", default=None, metavar="WINDOW",
        help="only kills inside this window: 90m, 24h, 7d or an ISO instant")
    parser.add_argument(
        "--top", type=int, default=DEFAULT_TOP, metavar="N",
        help="rows to print, largest resident memory first (default: %d)"
             % DEFAULT_TOP)
    args = parser.parse_args(argv)

    if args.top < 1:
        parser.error("--top must be at least 1")

    try:
        text = read_text(args.source)
        cutoff = parse_window(args.since) if args.since else None
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    victims, undated, unreadable = parse(text)
    if cutoff is not None:
        victims = [v for v in victims
                   if v["stamp"] is None or v["stamp"] >= cutoff]
    if undated and cutoff is not None:
        print("NOTE %d kill(s) have no timestamp and were kept" % undated,
              file=sys.stderr)
    if unreadable:
        print("NOTE %d kill(s) have no anon-rss value" % unreadable,
              file=sys.stderr)

    if not victims:
        where = " in the window" if cutoff is not None else ""
        print("OK    no OOM kill%s" % where)
        return 0

    victims.sort(key=lambda v: (-v["rss_kb"], -(v["score"] or -1)))
    print("%6s %7s %5s %6s  %-16s %s"
          % ("PID", "RSS_MB", "ADJ", "SCORE", "PROCESS", "TIME"))
    for victim in victims[:args.top]:
        print("%6d %7d %5s %6s  %-16s %s"
              % (victim["pid"],
                 victim["rss_kb"] // 1024,
                 "-" if victim["adj"] is None else victim["adj"],
                 "-" if victim["score"] is None else victim["score"],
                 victim["comm"][:16],
                 victim["stamp"].strftime("%H:%M:%S") if victim["stamp"] else "-"))
    worst = victims[0]
    where = " in the window" if cutoff is not None else ""
    print("FINDING %d OOM kill%s%s"
          % (len(victims), "" if len(victims) == 1 else "s", where))
    print("ALERT %s pid %d, %dMB, adj %s"
          % (worst["comm"], worst["pid"], worst["rss_kb"] // 1024,
             "-" if worst["adj"] is None else worst["adj"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
