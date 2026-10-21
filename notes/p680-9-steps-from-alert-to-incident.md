---
id: p680
title: "9 steps from alert to incident"
slug: 9-steps-from-alert-to-incident
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, DevOps, OnCall, Python]
source: "LinkedIn post P680 · IR series"
linkedin_date: 2031-01-30
design: steps
---

# 9 steps from alert to incident

The alert arrives, and nine small decisions follow. Most teams make seven of them and skip the two that matter: the dedupe and the handoff.

## Quick reference

### Detect — Name the signal in two commands

```bash
# List what is firing now, not what emailed.
amtool alert query --active
# Start the clock once, in UTC, before you act.
date -u +%Y-%m-%dT%H:%M:%SZ
# Count incidents; exit 1 means too much noise.
python3 alert_dedupe.py alerts.json
```

### Triage — Turn facts into a severity and a scope

```bash
# Turn users, data and revenue into SEV1 to SEV4.
python3 severity_classify.py inc.json
# Count the transitive dependents before restart.
python3 blast_radius.py graph.json api
# Merge every source into one ordered clock.
python3 incident_timeline.py *.json
```

### Declare — Give the incident an owner

- **pd incident:create -S api -t "API 5xx"** — One id, one channel, one severity on the record.
- **pd incident:ack -i INC-1042** — Acknowledge the page before the investigation.
- `python3 handoff_brief.py inc rota` — Hand over a ranked brief, not a paragraph.

## Explained

### Detect

`amtool alert query --active` lists what is firing right now, not what the inbox remembers. `date -u +%Y-%m-%dT%H:%M:%SZ` starts the incident clock in UTC, and every later timestamp is compared to it. `python3 alert_dedupe.py alerts.json` turns the pages into incidents; its exit code 1 is the noise finding, not a failure.

### Triage

`python3 severity_classify.py inc.json policy.json` turns users, data, revenue and duration into a declared severity. `python3 blast_radius.py graph.json api` counts who depends on the failing service, transitively. `python3 incident_timeline.py` merges alerts, deploys, chat and logs into one order.

### Declare

pd incident:create -S api -t "API 5xx" gives the incident one id and one channel. pd incident:ack -i INC-1042 acknowledges the page before the investigation starts. `python3 handoff_brief.py inc.json rota.json` hands over a ranked brief, with the unacknowledged critical item on top.

The nine steps are not a checklist for its own sake. Each one produces a fact the next one needs: a count, a severity, a scope, an owner.

> **The honest caveat:** the ninth step is not the end. The brief is the first input to the next shift, and it is only as good as the tracker behind it.

> **The lesson:** detect, triage, declare, in that order, with one fact from each step.

## In one line

> **Detect, triage, declare.** Three groups, nine commands, one order that holds.

**Declare after triage:** pd incident:create -S api -t API
