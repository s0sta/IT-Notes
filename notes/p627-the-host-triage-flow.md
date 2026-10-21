---
id: p627
title: "The host triage flow"
slug: the-host-triage-flow
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Linux, SRE, DevOps, IncidentResponse]
source: "LinkedIn post P627 · ShellSec series"
linkedin_date: 2030-09-29
design: architecture
---

# The host triage flow

At 03:00 you have an alert, a host and no plan. Triage is a flow with three tiers, and each tier has exactly one job.

## Quick reference

- **Tier 1 · Signal:** Alert fires (ALERT) · Host is slow (HOST)
- **Tier 2 · Check:** Run the script (CHECK) · Read the log (LOG)
- **Tier 3 · Decide:** Fix now (FIX) · Escalate (ESC)

**Request flow:** Alert fires → Run the script → Fix now; Alert fires → Read the log → Escalate; Host is slow → Run the script; Host is slow → Read the log

**Around it:** Alertmanager (ALRT) · journald (JRNL) · Runbook (BOOK)

## Explained

### Signal

The alert tier is what fired: a disk threshold, a failed unit, a listener that should not exist. The host tier is what the box feels like: load, memory, a shell that answers slowly. Both are inputs, not answers. A signal is allowed to be noisy; it is not allowed to be ignored.

### Check

The script tier is the check you wrote while the system was calm: `log_rotate_check.sh`, `user_audit.sh`, `open_ports.sh`. The log tier is the witness: journalctl, dmesg, the last 200 lines before the restart. A check is repeatable and has an exit code. A log is evidence, and it does not care what you expected.

### Decide

The fix tier is the change you can explain and reverse. The escalate tier is the one you hand over with the evidence attached. Fix what you understand; escalate what you do not. The boundary is the whole skill.

### The habit

Write the check before the incident, and give the decision a name. At 3 a.m. you execute a plan, you do not design one. Around the flow sit three tools: Alertmanager routes the signal, journald keeps the log, and the runbook names the decision.

> **The honest caveat:** a noisy signal trains people to skip the check, which is how a real alert gets missed.

> **The lesson:** signals are cheap, checks are scripted, decisions are named.

## In one line

> **Signal, check, then decide.** Three tiers, one flow, and a name for every step.

**Run the check:** bash `log_rotate_check.sh /var/log`
