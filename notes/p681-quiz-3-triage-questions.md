---
id: p681
title: "Quiz: 3 triage questions"
slug: quiz-3-triage-questions
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, OnCall, DevOps, CyberSecurity]
source: "LinkedIn post P681 · IR series"
linkedin_date: 2031-02-02
design: quiz
---

# Quiz: 3 triage questions

Phase one closes with three questions. Each one comes from a tool in this block, and each one is a decision you make before the incident is declared.

## Quick reference

**Q1. Why dedupe before paging?**

- a) A page is noise; an incident is a fact
- b) Every alert deserves its own page
- c) Dedupe makes the dashboard faster

> **Answer:** a) A page is noise; an incident is a fact. Eleven alerts with five fingerprints are five incidents. The fingerprint gives the count first, so the pager carries an incident id, not eleven alert ids.

**Q2. What does blast radius measure?**

- a) The transitive services that depend on it
- b) The failing service's own health check
- c) The number of pods in the namespace

> **Answer:** a) The transitive services that depend on it. The dependents, not the failing service. A green database can still take down checkout, mobile and admin; reverse the graph before calling it contained.

**Q3. Why does a handoff need unacked items?**

- a) An unacked page has no owner yet
- b) Unacked pages are always SEV1
- c) The night shift cannot write notes

> **Answer:** a) An unacked page has no owner yet. An unacknowledged page has no owner, and an incident without an owner is not being worked. Put it on top and exit 1 when it is critical.

## Explained

### Question one

Why dedupe before paging? Because a page is an interruption and an incident is a fact. Eleven alerts with five fingerprints are five incidents, and paging on all eleven wakes the same person five times. The fingerprint gives you the incident count first, then the pager can carry the incident id rather than the alert id.

### Question two

What does blast radius measure? The services that transitively depend on the failing one, not the failing service's own health. A database with a green health check can still take down checkout, mobile and admin. Reverse the graph and count the dependents before you call the incident contained.

### Question three

Why does a handoff need unacked items? Because an unacknowledged page has no owner, and an incident without an owner is not being worked. The brief must put that item on top and exit non-zero when it is critical, so the next shift cannot mistake a written summary for a transfer of responsibility.

> **The honest caveat:** the answers are easy. At 03:00 you get one command and one minute, so the habit is knowing which answer applies.

> **The lesson:** dedupe the noise, measure the reach, and hand off the unacked page.

## In one line

> **Three answers, one pager.** The tool names the cause; the cause names the fix.

**Check your answer**

```bash
python3 alert_dedupe.py alerts.json
```
