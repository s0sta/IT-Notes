---
id: p678
title: "Triage commands for the first ten minutes"
slug: triage-commands-for-the-first-ten-minutes
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, OnCall, DevOps, CommandLine]
source: "LinkedIn post P678 · IR series"
linkedin_date: 2031-01-26
design: cheatsheet
---

# Triage commands for the first ten minutes

The first ten minutes of an incident are a reading exercise. These are the commands that answer what is firing, when it started, what it touches and what the next person must know. Four blocks, one order.

## Quick reference

### Alerts

```bash
amtool alert query
amtool silence add alertname=DiskFull
curl -s localhost:9093/api/v2/alerts
promtool check rules rules.yml
jq '.[] | .fingerprint' alerts.json
```

### Timeline

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
journalctl -u api --since 03:00
git log --since=03:00 --oneline
kubectl rollout history deploy/api
jq -r '.[].started_at' alerts.json
```

### Scope

```bash
kubectl get pods -A -o wide
kubectl get endpoints payments
ss -tnp | grep :5432
dig +short payments.internal
curl -s localhost:8080/healthz
```

### Handoff

```bash
pd incident:list -s open
pd incident:ack -i INC-1042
pd incident:notes -i INC-1042 -n handoff
jq '.primary,.secondary' rota.json
date -u +%H:%M
```

## Explained

### Alerts

`amtool alert query` lists what is firing now, not what emailed at 03:00. amtool silence add alertname="DiskFull" stops a known repeat at the source. `curl -s localhost:9093/api/v2/alerts` returns the raw payload, and `promtool check rules rules.yml` proves the rule file still parses.

### Timeline

`date -u` gives the clock in UTC, which is the only clock a postmortem can use. `journalctl -u api --since 03:00` reads the service log from the incident window. `git log --since=03:00 --oneline` shows the change before the alert, and `kubectl rollout history deploy/api` shows the last revision.

### Scope

`kubectl get pods -A -o wide` shows what is running and where. `ss -tnp | grep :5432` finds live database connections. `kubectl get endpoints payments` shows whether the service has any healthy backends left, and `dig +short payments.internal` answers whether the name still resolves.

### Handoff

pd incident:list -s open lists the open incidents. pd incident:ack -i INC-1042 acknowledges the page, and pd incident:notes -i INC-1042 -n handoff writes the handoff line into the incident. `jq '.primary,.secondary' rota.json` names the next shift.

> **The honest caveat:** the first three blocks only read. The handoff block adds an acknowledgement and a note, so say who did it and when.

> **The lesson:** read the signal, the clock, the scope and the rota, then act once.

## In one line

> **Read, then command.** Four blocks, in the order the first ten minutes need.

**Start with alerts**

```bash
amtool alert query
```
