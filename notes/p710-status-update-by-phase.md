---
id: p710
title: "Status update by phase"
slug: status-update-by-phase
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, StatusPage, CyberSecurity, DevOps]
source: "LinkedIn post P710 · IR series"
linkedin_date: 2031-04-10
design: matrix
---

# Status update by phase

Three status updates, three different jobs. The phase decides what the page must contain, and a template that asks for the same six fields every time makes the difference visible.

## Quick reference

| | **Investigating** | **Identified** | **Resolved** |
|:--|:--|:--|:--|
| What happened | An alert, scope unknown | A named failure | The fix, verified |
| Impact | Being measured | Numbers and scope | Final count |
| Action | Looking, nothing changed | Contained, fixing | Rolled back, watched |
| ETA | None promised | A time you will hold | When we close |
| Next update | Inside 15 minutes | At the promised time | Before the close |
| Owner | Incident lead | Incident lead | Service owner |

**How to pick**

- **Investigating** → name the symptom and the next update time.
- **Identified** → put numbers on the impact and hold the ETA.
- **Resolved** → say what changed and what is still watched.

## Explained

What happened. Investigating names the symptom, not the cause: checkout errors, scope unknown. Identified names the failure: a bad release, one service, 4.1 per cent of card payments. Resolved names what changed, and what is still being watched.

Impact. Investigating measures it, identified quantifies it with a scope, and resolved closes the count. A page that keeps saying significant impact after the fix is a page nobody trusts.

Action. Investigating is a verb with no object yet. Identified is containment and a fix in progress. Resolved is the rollback or the patch, plus the monitoring that follows it.

ETA. Investigating promises no time for the fix, only a time for the next update. Identified holds a time you can defend. Resolved needs none, because the next communication is the close.

Next update. Fifteen minutes while investigating, the promised time once identified, and one final update before close.

Owner. The incident lead owns the first two columns; the service owner owns the third, because the follow-up outlives the incident.

The grid lays the three phases side by side, so a missing cell is a blank you can see before you publish.

> **The honest caveat:** phases overlap in a real incident, and a page that lags the room is worse than one that admits it.

> **The lesson:** the phase is a contract about what the update must contain.

## In one line

> **The phase decides what the update says.** Three columns, one template, six fields that must not be blank.

**Draft the update**

```bash
python3 status_update.py inc.json identified
```
