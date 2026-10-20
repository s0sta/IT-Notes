---
id: p138
title: "The first 30 minutes of an outage"
slug: the-first-30-minutes-of-an-outage
sections: [it, devsecops]
topic: "IT operations & incidents"
tags: [IncidentResponse, SRE, DevOps, OnCall, ITOperations]
source: "LinkedIn post P138 · IT series"
linkedin_date: 2027-08-15
design: timeline
---

# The first 30 minutes of an outage

When production breaks, the difference between a 10-minute blip and a 2-hour outage is rarely the fix itself. It is how the first 30 minutes are handled.

## Quick reference

| Time | Step | What happens |
|:--|:--|:--|
| **00:00** | Alert fires | Error rate crosses the threshold. The pager goes off. |
| **00:02** | Acknowledge | One person owns it. Open the incident channel. |
| **00:05** | Assess | What changed? Last deploy, config, or a traffic spike. |
| **00:10** | Stop the bleeding | Roll back or scale out before you root-cause. |
| **00:20** | Confirm recovery | Metrics back to normal. Users are unblocked. |
| **00:30** | Write it down | Capture the timeline while it is still fresh. |

## Explained

00:00 - Alert fires. The error rate, latency or an uptime check crosses a threshold and the pager goes off. Good alerts are few and meaningful, so this one is trusted.

00:02 - Acknowledge. One person takes ownership and opens the incident channel. Clear ownership stops the two worst failure modes: everyone assuming someone else has it, or five people changing things at once.

00:05 - Assess. The first question is almost always "what changed?" The last deploy, a config change, an expired certificate, or a traffic spike. git log, the deploy history and the dashboards answer this fast.

00:10 - Stop the bleeding. This is the key mindset: restore service before you fully understand the cause. Roll back the deploy, scale out, fail over, or disable the broken feature. Users do not care why it broke, they care that it works.

00:20 - Confirm recovery. Watch the metrics return to normal and verify from the outside, as a user would. Do not declare victory from a single green check.

00:30 - Write it down. Capture the timeline and the actions while memory is fresh. This becomes the blameless postmortem that stops it happening again.

The hardest discipline is resisting the urge to debug deeply while users are down. Stabilise first. Root cause after.

Calm is a technical skill, and it can be practised.

## In one line

> **Calm is a technical skill.** Stabilise first. Understand the root cause after.

**The first move:** acknowledge, then stop the bleeding
