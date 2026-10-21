---
id: p675
title: "A severity policy check"
slug: a-severity-policy-check
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, IncidentResponse, SRE, DevOps, OnCall]
source: "LinkedIn post P675 · IR series"
linkedin_date: 2031-01-19
design: code
script: severity_classify.py
---

# A severity policy check

The incident is declared SEV2 because the last one was SEV2. Six minutes later, customer data is in the logs and the status page is still quiet. The declared number was a feeling; the policy was never consulted.

## Quick reference

The full script is at the end of this note: `severity_classify.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 severity_classify.py /tmp/s15/si.json /tmp/s15/sp.json
```

**Example output**

```text
SUMMARY 4 incidents, 1 mismatch
MISMATCH INC-1042 declared SEV2, actual SEV1
```

## Explained

### What it does

`severity_classify.py` reads incidents and a written policy with three ascending thresholds for users, revenue and duration, plus a ranked data class. It takes the highest level any dimension reaches, turns that into SEV1 to SEV4, and flags every incident whose declared severity disagrees with the policy.

### What the screen shows

The panel loads the incidents and policy, scores four incidents, and prints SUMMARY 4 incidents, 1 mismatch, then MISMATCH INC-1042 declared SEV2, actual SEV1.

### How to run it

`python3 severity_classify.py /tmp/s15/si.json /tmp/s15/sp.json`. Exit 0 means every declaration matches, 1 means at least one mismatch, 2 means the policy or incident file is malformed. It writes nothing.

### The fix

Classify before you declare, then revise the declaration as facts arrive. A mismatch is not a failure by itself; an unexplained mismatch is. Write the reason on the incident: users, data, revenue or duration, and the threshold it crossed.

### Prevention

Review mismatches weekly. If SEV2 always means the previous incident, the policy is decoration and the status page is guesswork.

> **The honest caveat:** the policy is only as good as the numbers you feed it. Users affected is the hardest field to measure during an incident.

> **The lesson:** severity is a decision from four inputs, not a memory of the last outage.

## In one line

> **Declare the number you can defend.** A mismatch is a fact, not an argument.

**Classify, then declare**

```bash
python3 severity_classify.py inc.json
```

## Script: severity_classify.py

Download: [scripts/severity_classify.py](../scripts/severity_classify.py)

```python
#!/usr/bin/env python3
"""severity_classify.py - turn incident facts into a declared severity.

Severity is usually declared in the first two minutes, from a feeling and the
last incident. Then the facts arrive. This script reads the incident record
and a written policy, classifies each incident from users affected, data
class, revenue per hour and duration, and prints every place where the
declared severity and the policy disagree.

The policy JSON holds three ascending thresholds per numeric dimension: the
first is the SEV3 line, the second SEV2, the third SEV1. Data maps each
class to a level, from 0 (none) to 3 (regulated).

    {"users": [500, 5000, 50000],
     "revenue": [500, 5000, 50000],
     "duration": [30, 60, 120],
     "data": {"none": 0, "internal": 1, "customer": 2, "regulated": 3}}

The incidents file is a JSON list, or an object with an "incidents" list:

    {"id": "INC-1042", "title": "payments API 5xx", "declared": "SEV2",
     "users": 60000, "revenue": 12000, "duration": 130,
     "data": "customer"}

An incident takes the highest level any dimension reaches, so one SEV1 input
makes it a SEV1. "none" is the no-data value; every class must appear in the policy.

Usage:
    python3 severity_classify.py incidents.json policy.json
    python3 severity_classify.py incidents.json policy.json --only-mismatch
    python3 severity_classify.py --help

CI (fail a release review that leaves a declared severity unexplained):
    python3 severity_classify.py incidents.json policy.json || exit 1

Exit codes: 0 every declared severity matches the policy, 1 at least one
mismatch, 2 usage error or unreadable, empty or malformed input.

Read-only: opens the two files, compares them and prints. It writes nothing,
changes nothing and makes no network call.

By s0sta.com
"""
import argparse
import json
import sys

SEVERITIES = ("SEV1", "SEV2", "SEV3", "SEV4")
DIMENSIONS = ("users", "revenue", "duration")
POLICY_KEYS = ("users", "revenue", "duration", "data")


class InputError(Exception):
    """An input that cannot be classified."""


def read_json(path):
    """Return a decoded JSON document, or raise InputError."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except OSError as exc:
        raise InputError("%s: %s" % (path, exc.strerror or exc))
    except ValueError as exc:
        raise InputError("%s is not JSON: %s" % (path, exc))


def load_policy(path):
    """Return a validated policy, or raise InputError."""
    doc = read_json(path)
    if not isinstance(doc, dict):
        raise InputError("%s: expected a JSON object" % path)
    for key in POLICY_KEYS:
        if key not in doc:
            raise InputError("%s: missing %s" % (path, key))
    policy = {}
    for key in DIMENSIONS:
        values = doc[key]
        if not isinstance(values, list) or len(values) != 3:
            raise InputError("%s: %s needs three thresholds" % (path, key))
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                   for value in values):
            raise InputError("%s: %s thresholds must be numbers" % (path, key))
        if any(values[i] > values[i + 1] for i in range(2)):
            raise InputError("%s: %s thresholds must ascend" % (path, key))
        policy[key] = [float(value) for value in values]
    data = doc["data"]
    if not isinstance(data, dict) or not data:
        raise InputError("%s: data must map class names to levels" % path)
    classes = {}
    for name, rank in data.items():
        if not isinstance(name, str) or not name.strip():
            raise InputError("%s: data class names must be strings" % path)
        if (not isinstance(rank, int) or isinstance(rank, bool)
                or not 0 <= rank <= 3):
            raise InputError("%s: data level for %s must be 0 to 3"
                             % (path, name))
        classes[name.strip()] = rank
    if len(set(classes.values())) != len(classes):
        raise InputError("%s: data levels must be unique" % path)
    if 0 not in classes.values():
        raise InputError("%s: data needs a level 0 class" % path)
    policy["data"] = classes
    return policy


def load_incidents(path, policy):
    """Return validated incidents, or raise InputError."""
    doc = read_json(path)
    if isinstance(doc, dict):
        if "incidents" not in doc:
            raise InputError("%s: object needs an \"incidents\" list" % path)
        doc = doc["incidents"]
    if not isinstance(doc, list):
        raise InputError("%s: expected a list of incidents" % path)
    if not doc:
        raise InputError("%s: no incidents in input" % path)
    incidents = []
    for index, raw in enumerate(doc, start=1):
        where = "incident %d" % index
        if not isinstance(raw, dict):
            raise InputError("%s: expected an object" % where)
        incident_id = raw.get("id")
        declared = raw.get("declared")
        data = raw.get("data")
        title = raw.get("title", "")
        if not isinstance(incident_id, str) or not incident_id.strip():
            raise InputError("%s: missing id" % where)
        if declared not in SEVERITIES:
            raise InputError("%s: declared must be SEV1 to SEV4" % where)
        for key in DIMENSIONS:
            value = raw.get(key)
            if (not isinstance(value, (int, float)) or isinstance(value, bool)
                    or value < 0):
                raise InputError("%s: %s must be a non-negative number"
                                 % (where, key))
        if not isinstance(data, str) or not data.strip():
            raise InputError("%s: missing data class" % where)
        data = data.strip()
        if data not in policy["data"]:
            raise InputError("%s: unknown data class %r" % (where, data))
        if not isinstance(title, str):
            raise InputError("%s: title must be a string" % where)
        incidents.append({
            "id": incident_id.strip(),
            "title": title.strip(),
            "declared": declared,
            "users": float(raw["users"]),
            "revenue": float(raw["revenue"]),
            "duration": float(raw["duration"]),
            "data": data,
        })
    return incidents


def level(value, thresholds):
    """Return 0 to 3: how many ascending thresholds the value reaches."""
    return sum(1 for threshold in thresholds if value >= threshold)


def classify(incident, policy):
    """Return (actual severity, level, reason)."""
    levels = {
        "users": level(incident["users"], policy["users"]),
        "revenue": level(incident["revenue"], policy["revenue"]),
        "duration": level(incident["duration"], policy["duration"]),
        "data": policy["data"][incident["data"]],
    }
    top = max(levels.values())
    actual = "SEV%d" % (4 - top)
    if top == 0:
        return actual, top, "no threshold met"
    if levels["users"] == top:
        reason = "users %g >= %g" % (incident["users"],
                                     policy["users"][top - 1])
    elif levels["revenue"] == top:
        reason = "revenue %g/h >= %g" % (incident["revenue"],
                                         policy["revenue"][top - 1])
    elif levels["duration"] == top:
        reason = "duration %g min >= %g" % (incident["duration"],
                                            policy["duration"][top - 1])
    else:
        reason = "data %s" % incident["data"]
    return actual, top, reason


def report(incidents, policy, only_mismatch):
    """Return (finding, lines) for the incident set."""
    classified, mismatches = [], []
    for incident in incidents:
        actual, _top, reason = classify(incident, policy)
        classified.append((incident, actual, reason))
        if actual != incident["declared"]:
            mismatches.append((incident, actual, reason))
    lines = []
    for incident, actual, _reason in classified:
        if only_mismatch and actual == incident["declared"]:
            continue
        detail = ("%s %s" % (incident["id"],
                             ("(%s) " % incident["title"]) if incident["title"] else ""))
        lines.append("CLASSIFY %-34s %s (declared %s) users %g, %g/h, %g min, data %s"
                     % (detail, actual, incident["declared"],
                        incident["users"], incident["revenue"],
                        incident["duration"], incident["data"]))
    lines.append("SUMMARY %d incident%s, %d mismatch%s"
                 % (len(classified), "" if len(classified) == 1 else "s",
                    len(mismatches), "" if len(mismatches) == 1 else "es"))
    for incident, actual, _reason in mismatches:
        lines.append("MISMATCH %s declared %s, actual %s"
                     % (incident["id"], incident["declared"], actual))
    for incident, actual, reason in mismatches:
        lines.append("WHY %s %s (%s)" % (incident["id"], reason, actual))
    if not mismatches:
        lines.append("OK all declared severities match")
    return bool(mismatches), lines


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Classify incident severity from a written policy (read-only).")
    parser.add_argument("incidents", help="incidents JSON")
    parser.add_argument("policy", help="severity policy JSON")
    parser.add_argument(
        "--only-mismatch", action="store_true",
        help="print only the incidents whose declared severity is wrong")
    args = parser.parse_args(argv)

    try:
        policy = load_policy(args.policy)
        incidents = load_incidents(args.incidents, policy)
    except InputError as exc:
        print("ERROR %s" % exc, file=sys.stderr)
        return 2

    finding, lines = report(incidents, policy, args.only_mismatch)
    for line in lines:
        print(line)
    return 1 if finding else 0


if __name__ == "__main__":
    sys.exit(main())
```
