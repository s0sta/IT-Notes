---
id: p719
title: "Four learning failures"
slug: four-learning-failures
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [Python, SRE, Postmortem, DevOps, CyberSecurity]
source: "LinkedIn post P719 · IR series"
linkedin_date: 2031-05-01
design: explainer
---

# Four learning failures

Four postmortems, four different failures, and one shape: nobody checked the thing that was supposed to prevent the repeat. The incidents looked unrelated until the checks were written down.

## Quick reference

### The detection gap

- A technique in the actor report
- No enabled rule carries its id
- Invisible, not missed
- Fix: one rule, one owner, one date

### The stale runbook

- Steps for a service that changed
- Last reviewed two releases ago
- The on-call follows them anyway
- Fix: a review date and a drill

### The noisy alert

- Fifty fires, two actions
- The team learns to ignore the pager
- The real alert waits behind the noise
- Fix: a signal ratio and a review

### The unverified control

- The policy says MFA is on
- The export says false
- Nobody opened the export
- Fix: dated evidence and a check

> **Note:** Four failures, one shape: the check that would have caught it was never run.

## Explained

### The detection gap

A technique appears in the actor report, but no enabled rule covers it. The activity was not missed by the analyst; it was invisible to the tooling.

### The stale runbook

The steps describe a service that changed shape two releases ago. The on-call follows them, makes the outage longer, and loses trust in the page.

### The noisy alert

The rule fires fifty times a month and is actioned twice. The team learns to ignore the pager, and the one real alert waits behind a month of expected ones.

### The unverified control

The policy says MFA is on, the export says false, and nobody looked. The control had been off long enough to become the normal state.

### What they share

Each failure has a measurement: a coverage list, a review date, a signal ratio, an evidence file. None of them needs a new tool; each needs a check that runs on a schedule and has an owner. A postmortem that names the check, the owner and the date is already a control.

> **The honest caveat:** a check that runs once is a screenshot. The schedule is the control.

> **The lesson:** learning is a check, not a meeting.

## In one line

> **What nobody checks comes back.** A control you never test is a control you borrowed.

**Measure the loop**

```bash
python3 runbook_freshness.py docs
```
