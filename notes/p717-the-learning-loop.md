---
id: p717
title: "The learning loop"
slug: the-learning-loop
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [Python, SRE, IncidentResponse, DevOps, Security]
source: "LinkedIn post P717 · IR series"
linkedin_date: 2031-04-27
design: architecture
---

# The learning loop

Every postmortem ends with lessons learned, and most of them end there. The action list closes, the document is filed, and the next incident finds the same gap.

## Quick reference

- **Detect:** Coverage map (COV) · Noise ranking (NOISE)
- **Fix:** Action list (ACT) · Named owner (OWN)
- **Verify:** Control check (CTRL) · Drill calendar (DRILL)

**Request flow:** Noise ranking → Named owner → Drill calendar → Coverage map → Action list → Control check

**Around it:** Postmortem (PM) · Risk register (RISK) · Change log (CHG)

## Explained

### What it does

The learning loop has three tiers. Detect holds the coverage map and the noise ranking: which techniques have an enabled rule, and which alerts earn their page. Fix holds the actions, each with an owner and a date. Verify holds the control checks and the drills that prove the fix still works.

### How to use it

Read it as a loop, not a queue. A coverage gap becomes an action with an owner. An action becomes a control that can be checked. A control check that fails becomes next week's fix; a drill that fails becomes next week's detection work. The arrows down are the handoffs; the arrow back is the reason the loop is a loop.

### The fix

Give each tier one weekly output: the coverage diff, the open actions with owners and dates, and the control evidence with the last drill. Three artefacts, one owner each, reviewed on the same day.

### Prevention

Put the loop on the postmortem template. A finding that cannot name its tier, its owner and its evidence is not an action yet.

> **The honest caveat:** a loop with no owner is a diagram. The drawing is the easy part.

> **The lesson:** learning is a system with inputs, owners and checks, not a meeting.

## In one line

> **A loop that closes is a system.** Three tiers, one owner each, reviewed on the same day.

**Close the loop**

```bash
python3 control_verify.py ctl.json exports
```
