---
id: p679
title: "Four triage mistakes"
slug: four-triage-mistakes
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, DevOps, OnCall, CyberSecurity]
source: "LinkedIn post P679 · IR series"
linkedin_date: 2031-01-28
design: explainer
---

# Four triage mistakes

Triage fails in the same four places every time, and none of them is a tooling problem. The tools are fine; the order is wrong.

## Quick reference

### Alert storms

- One disk fires every five minutes, a new thread each time
- Ten versions of one incident hide the second failure
- A stable fingerprint turns eleven alerts into five
- A rule budget stops the repeat before the pager

### No timeline

- Alerts, deploys, chat and logs keep four clocks
- Nobody can say what happened first
- Merge the clocks and the gap becomes visible
- Without it, the postmortem is memory

### Unknown scope

- The failing service is healthy again, so it closes
- Then checkout, mobile and admin fail with it
- Reverse the graph and count the dependents
- Declare recovery only after the closure

### Silent handoff

- The night shift writes a paragraph, not a brief
- The day shift reads the first line and stops
- The unacked SEV1 stays unacked all day
- Rank the open items and exit 1 on a critical page

> **Note:** Four ways triage loses the incident.

## Explained

### Alert storms

One failing disk fires every five minutes, and every webhook opens a new thread. The channel fills with ten versions of one incident, and the real second failure arrives unseen. A stable fingerprint and a rule budget turn eleven alerts into five incidents before anyone is paged.

### No timeline

The alert is in one system, the deploy in another, the chat in a third and the log on the host. Nobody can say what happened first. Merge the clocks and the gap becomes visible; without it, the postmortem is a story about memory.

### Unknown scope

The failing service is healthy again, so the incident is closed. Then checkout, mobile and admin fail, because they depended on it. Reverse the graph and count the dependents before you declare recovery, not after.

### Silent handoff

The night shift writes a paragraph, the day shift reads the first line, and the unacknowledged SEV1 stays unacknowledged. A brief that ranks the open items and exits 1 on a critical unacked page is not bureaucracy; it is the only part of the handoff that cannot be skipped.

> **The honest caveat:** fixing all four at once is a programme, not a sprint. Start with the one that cost you the last incident.

> **The lesson:** triage fails in four places, and all four are decisions, not tools.

## In one line

> **Triage fails in four places.** The tools are fine; the order is wrong.

**Check the order**

```bash
python3 alert_dedupe.py alerts.json
```
