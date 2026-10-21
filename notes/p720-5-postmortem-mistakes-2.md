---
id: p720
title: "5 postmortem mistakes"
slug: 5-postmortem-mistakes-2
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [Python, SRE, Postmortem, IncidentResponse, DevOps]
source: "LinkedIn post P720 · IR series"
linkedin_date: 2031-05-04
design: dontdo
---

# 5 postmortem mistakes

The postmortem is over, the document is published, and six weeks later the same incident is back. The five mistakes are predictable, and each one leaves the system unchanged.

## Quick reference

**1.** ❌ **Name the engineer** — Blame ends the questions early.  
✅ **Name the control that failed** — A missing guard can be fixed; a person cannot.

**2.** ❌ **Action with no owner** — Everyone's action is nobody's action.  
✅ **One name and one date** — Ownership and a deadline make it real.

**3.** ❌ **No deadline on the fix** — Work without a date never competes.  
✅ **Date it in the tracker** — A date turns intent into a commitment.

**4.** ❌ **Mark it fixed and move on** — An assertion is not a test.  
✅ **Re-run the control check** — Evidence closes the item; a claim does not.

**5.** ❌ **Keep the lessons internal** — The next team repeats the incident.  
✅ **Publish the write-up** — One page saves the next on-call a night.

## Explained

### The five

1. **Blame the engineer.** The person who clicked is the end of the story, not the start. Name the control that should have stopped the click, and the missing guard becomes the action.
   \2. Leave the action unowned. An action without a name belongs to everyone, which means it belongs to nobody. One name and one date per action.
   \3. Set no deadline. A fix with no date never competes with the next feature. Put the date in the tracker and review it like a release.
   \4. Never verify the fix. "Marked fixed" is an assertion; a re-run control check is evidence. Close the action only when the check passes.
   \5. Keep the lessons internal. The next team meets the same failure with the same surprise. Publish the write-up where the on-call can find it.

### What they share

Every one postpones the proof. The meeting ends, the document is filed, and the next on-call starts from zero.

> **The honest caveat:** blameless does not mean consequence-free. Accountability belongs to the action and the system, not to the person who happened to be on call.

> **The lesson:** a postmortem is a to-do list, and the list is the point.

## In one line

> **A postmortem is a to-do list.** If nothing changed on Monday, it was a meeting.

**Close one item:** assign one action, set one date
