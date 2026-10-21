---
id: p577
title: "The incident triage path"
slug: the-incident-triage-path
sections: [it, devsecops]
topic: "IT operations & incidents"
tags: [SRE, IncidentResponse, DevOps, OnCall, Linux]
source: "LinkedIn post P577 · PythonFixes series"
linkedin_date: 2030-06-04
design: architecture
---

# The incident triage path

The page fires at 03:12. By 03:14 four people are in four terminals, and two of them are already restarting things. The host did not fail four times; four people skipped the same path.

## Quick reference

- **Alert:** Pager (PAGE) · Dashboard (DASH)
- **Diagnose:** Triage script (RUN) · Kernel log (DMESG) · App log (LOG)
- **Fix:** Rollback (ROLL) · Restart (BOOT)

**Request flow:** Pager → Triage script → Kernel log → Rollback; Triage script → App log → Restart; Dashboard → Triage script

**Around it:** Exit code (EXIT) · Runbook (RUN) · Timeline (TIME)

## Explained

### Alert

The alert tier is two surfaces, not one. The pager wakes a human, and the dashboard shows whether anything else is on fire. Neither may touch the host. Their only job is to open the runbook and start the clock, because the timestamp is the first fact of the incident.

### Diagnose

The diagnose tier is one script and two logs. The script is read-only and answers with an exit code: 0 clean, 1 finding, 2 the check itself broke. The kernel log says whether an OOM kill or a disk error came first, and the app log says what the process was doing. Read both before you change either.

### Fix

The fix tier has two moves. Rollback undoes the last change. Restart clears the state that the change left behind. Pick one, say which one out loud, and write the time down.

Under the three tiers sit the three things that outlive the incident: the exit code the script returned, the runbook someone will read next time, and the timeline that turns a bad night into a postmortem.

> **The honest caveat:** the order matters more than the speed. A restart at 03:13 destroys the state that would have explained the failure at 03:30.

> **The lesson:** triage is a path, not a conversation.

## In one line

> **Alert, diagnose, then fix.** Three tiers, and only one of them may change the host.

**Open the runbook**

```bash
less runbooks/host-down.md
```
