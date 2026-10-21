---
id: p519
title: "Anatomy of a network incident"
slug: anatomy-of-a-network-incident
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [Networking, IncidentResponse, SRE, OnCall, DevOps]
source: "LinkedIn post P519 · Network series"
linkedin_date: 2030-01-20
design: timeline
---

# Anatomy of a network incident

The alert says latency, the graph says packet loss, and the last deploy was four hours ago. A network incident has six stages: alert, localise, mitigate, fix, verify and review. Most teams skip the last two.

## Quick reference

| Time | Step | What happens |
|:--|:--|:--|
| **T+0** | Alert | p95 crosses the SLO; the on-call opens the network board. |
| **T+5** | Localise | Which region, which hop: mtr, the AZ split, the deploy log. |
| **T+15** | Mitigate | Shift traffic, add capacity or roll back; stop the bleeding first. |
| **T+1h** | Fix | Repair the cause: a route, a full queue, a health check that lied. |
| **T+2h** | Verify | Watch p95 and loss through a full traffic cycle, not five quiet minutes. |
| **T+1d** | Review | Blameless: what the alert missed, what the runbook lacked, who owns it. |

## Explained

### First hour

At T+0 the p95 alert crosses the SLO and the on-call opens the network board, not the service dashboard. The first question is not why; it is how many users and which regions. At T+5 the job is to localise: which region, which hop, which direction. mtr shows where the RTT steps up, the per-AZ split shows whether every zone is affected, and the deploy log says whether anything changed.

### Repair

At T+15 mitigation starts before diagnosis ends: withdraw the bad route, shift traffic to the healthy region, add capacity or roll back. Stopping the bleeding is a separate skill from finding the cut. At T+1h the fix repairs the cause, whether that is a route, a full queue, a health check that never failed or an MTU that only breaks on one path.

### After

At T+2h verification watches p95 and loss through a full traffic cycle, not five quiet minutes; a cache warm-up can hide a broken path for ten minutes. At T+1d the review asks what the alert missed and what the runbook lacked, and assigns both an owner and a date.

> **The honest caveat:** the timeline is reconstructed from chat and alert timestamps that disagree by minutes, so record decisions as you make them.

> **The lesson:** mitigation buys the time a root cause needs.

## In one line

> **Stop the bleeding, then find the cut.** Mitigation buys the time a root cause needs.

**Check the path**

```bash
mtr -rw --report-cycles 10 10.0.0.5
```
