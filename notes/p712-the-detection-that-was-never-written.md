---
id: p712
title: "The detection that was never written"
slug: the-detection-that-was-never-written
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, DetectionEngineering, SOC, ThreatHunting, CyberSecurity]
source: "LinkedIn post P712 · IR series"
linkedin_date: 2031-04-15
design: code
script: detection_gap.py
---

# The detection that was never written

The technique was in the threat report in January. In October the same actor used it again. The SIEM had no rule, so nothing could fire.

## Quick reference

The full script is at the end of this note: `detection_gap.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 detection_gap.py tech.json det.json
```

**Example output**

```text
COVERAGE 4/8 techniques, 2 high gaps
GAP T1059, T1566 high relevance
```

## Explained

### What it does

`detection_gap.py` reads two lists. The list gives each technique a name, a relevance and its actors. The detection inventory gives each rule a technique and an enabled flag. A technique is covered only when at least one enabled rule carries its exact id. A disabled rule is a gap with a file: the rule exists, the detection does not.

### How to run it

`python3 detection_gap.py techniques.json detections.json`, then the same command in CI with || exit 1. It exits 0 when every technique at or above `--fail-on` is covered, 1 when one is not, and 2 on bad input.

### What the screen shows

The fourteen lines load both files, build the enabled set, compare it with the list, and print the coverage and high-relevance ids. On the dirty fixture: COVERAGE 4/8 techniques, 2 high gaps and GAP T1059, T1566 high relevance.

### The fix

Take the high gaps to the backlog with the actor attached. One rule, one owner, one date. A gap on a slide for a quarter is not a plan.

### Prevention

Run the check weekly from the list the threat report uses. When the list changes, the gaps change.

> **The honest caveat:** exact id matching does not roll sub-techniques up, and an existing rule has not been tested.

> **The lesson:** a detection you never wrote cannot fire.

## In one line

> **A gap you can name is a gap you can close.** A technique with no enabled rule is a gap, even when the rule exists.

**Map the gaps**

```bash
python3 detection_gap.py t.json d.json
```

## Script: detection_gap.py

Download: [scripts/detection_gap.py](../scripts/detection_gap.py)

```python
#!/usr/bin/env python3
"""Find techniques with no enabled detection and rank the gaps.

Reads a technique list and a detection inventory, then answers one question
per technique: is there at least one enabled rule that covers it?

The technique list is JSON, one object per technique:

    [{"id": "T1059", "name": "Command and Scripting Interpreter",
      "relevance": "high", "actors": ["APT29", "FIN7"]},
     {"id": "T1566", "name": "Phishing", "relevance": "high",
      "actors": ["APT29"]}]

The detection inventory is JSON, one object per rule:

    [{"technique": "T1059", "rule": "powershell-encoded", "enabled": true},
     {"technique": "T1566", "rule": "mail-forwarding-rule", "enabled": false}]

A technique is covered when at least one detection for the exact technique id
is enabled. A disabled rule does not count, because a rule that is off is a
detection that was never written. Matching is by exact id: a rule for
T1059.001 does not cover T1059, and the summary does not roll sub-techniques
up into their parent.

Usage:
    python3 detection_gap.py techniques.json detections.json
    python3 detection_gap.py techniques.json detections.json --fail-on medium

The default fail level is high: only a high-relevance gap exits 1. Use
--fail-on medium or --fail-on low to be stricter. An empty detection list is
valid and means every technique is a gap.

Exit codes: 0 no gap at or above the fail level, 1 at least one, 2 usage, or
a file that is missing, unreadable, invalid or empty.

CI (weekly, fail the job when a high-relevance technique is uncovered):
    python3 detection_gap.py techniques.json detections.json || exit 1

Cron (Monday 06:00, mail the gap report):
    0 6 * * 1 python3 /opt/s0sta/detection_gap.py /etc/s0sta/techniques.json \
        /etc/s0sta/detections.json

The script is read-only: it reads both files, prints the coverage and writes
nothing. It tells you where the list has no rule; it does not tell you whether
the rule that exists would fire. Run a purple-team test for that.

Standard library only, Python 3.8+.

By s0sta.com
"""
import argparse
import json
import sys

RANK = {"high": 0, "medium": 1, "low": 2}


class InputError(Exception):
    """Anything that should end the run with exit code 2."""


def load_list(path, label, allow_empty=False):
    """Return a list from a JSON file, or raise InputError."""
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise InputError("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(doc, list):
        raise InputError("%s has no %s list" % (path, label))
    if not doc and not allow_empty:
        raise InputError("%s has an empty %s list" % (path, label))
    return doc


def technique_fields(item, number):
    """Validate one technique entry and return (id, name, relevance, actors)."""
    if not isinstance(item, dict):
        raise InputError("technique %d is not an object" % number)
    tech_id = item.get("id")
    name = item.get("name")
    relevance = item.get("relevance")
    actors = item.get("actors", [])
    if not isinstance(tech_id, str) or not tech_id:
        raise InputError("technique %d has no id" % number)
    if not isinstance(name, str) or not name:
        raise InputError("technique %s has no name" % tech_id)
    if relevance not in RANK:
        raise InputError("technique %s has no high, medium or low relevance" % tech_id)
    if not isinstance(actors, list) or any(not isinstance(a, str) for a in actors):
        raise InputError("technique %s actors must be a list of names" % tech_id)
    return tech_id, name, relevance, actors


def detection_fields(item, number):
    """Validate one detection entry and return (technique, rule, enabled)."""
    if not isinstance(item, dict):
        raise InputError("detection %d is not an object" % number)
    technique = item.get("technique")
    rule = item.get("rule")
    enabled = item.get("enabled")
    if not isinstance(technique, str) or not technique:
        raise InputError("detection %d has no technique" % number)
    if not isinstance(rule, str) or not rule:
        raise InputError("detection %d has no rule" % number)
    if not isinstance(enabled, bool):
        raise InputError("detection %s has no boolean enabled" % rule)
    return technique, rule, enabled


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Map detection coverage against a technique list and "
                    "report every technique with no enabled rule.",
        epilog="Exit codes: 0 covered, 1 gap at or above --fail-on, "
               "2 usage or input error.")
    parser.add_argument("techniques", help="JSON list of techniques")
    parser.add_argument("detections", help="JSON list of detection rules")
    parser.add_argument("--fail-on", choices=("high", "medium", "low"),
                        default="high",
                        help="lowest relevance that exits 1 (default: high)")
    args = parser.parse_args(argv)

    try:
        techniques = load_list(args.techniques, "techniques")
        detections = load_list(args.detections, "detections", allow_empty=True)

        seen = set()
        techs = []
        for number, item in enumerate(techniques, 1):
            tech_id, name, relevance, actors = technique_fields(item, number)
            if tech_id in seen:
                raise InputError("duplicate technique id %s" % tech_id)
            seen.add(tech_id)
            techs.append((tech_id, name, relevance, actors))

        enabled = {}
        disabled = {}
        for number, item in enumerate(detections, 1):
            technique, rule, on = detection_fields(item, number)
            if technique not in seen:
                print("WARN detection %s covers unknown technique %s"
                      % (rule, technique), file=sys.stderr)
                continue
            if on:
                enabled[technique] = enabled.get(technique, 0) + 1
            else:
                disabled[technique] = disabled.get(technique, 0) + 1
    except InputError as exc:
        print("ERR %s" % exc, file=sys.stderr)
        return 2

    gaps = []
    for tech_id, name, relevance, actors in techs:
        if tech_id not in enabled:
            gaps.append((tech_id, name, relevance, actors,
                         disabled.get(tech_id, 0)))
    gaps.sort(key=lambda g: (RANK[g[2]], g[0]))

    covered = len(techs) - len(gaps)
    high = sum(1 for g in gaps if g[2] == "high")
    print("COVERAGE %d/%d techniques, %d high gaps"
          % (covered, len(techs), high))
    for tech_id, name, relevance, actors, off in gaps:
        who = ", ".join(actors) if actors else "no actor listed"
        extra = ", %d disabled" % off if off else ""
        print("GAP %s %s %s (%s%s)"
              % (tech_id, relevance, name, who, extra))

    limit = RANK[args.fail_on]
    failing = [g for g in gaps if RANK[g[2]] <= limit]
    if failing:
        return 1
    if not gaps:
        print("OK every technique has an enabled detection")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
