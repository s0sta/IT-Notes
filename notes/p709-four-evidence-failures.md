---
id: p709
title: "Four evidence failures"
slug: four-evidence-failures
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, DFIR, CyberSecurity, SRE, Postmortem]
source: "LinkedIn post P709 · IR series"
linkedin_date: 2031-04-08
design: explainer
---

# Four evidence failures

Four evidence failures turn up in reviews, and none of them is a missing tool. Every one is a step somebody skipped while the incident was still moving.

## Quick reference

### No hash

- A copy nobody hashed is a claim, not evidence
- The bytes may be right; you cannot show it
- Hash at collection, on the host, not later

### No chain

- Who held the disk, and on which day
- A bundle with an unknown middle is unproven
- Storage, handover, hash, repeat

### No timeline

- Memory orders events by who is speaking
- A row with no source is a memory
- Export it while the incident still runs

### No owner

- An unowned action never closes
- A name and a date, at write time
- A duplicate points at its original

> **Note:** The tools were fine. The process left a gap a reviewer could walk through.

## Explained

### No hash

A copy that nobody hashed is a claim. The bytes may be right; you cannot show it. Hash at collection, on the host, and keep the digest beside the file name where a reviewer can find it.

### No chain

Who held the disk, and on which day? A bundle that moves between laptops and shared drives with no record has an unknown middle. An unbroken list of storage, handover, hash, repeat beats a good story every time.

### No timeline

Memory orders events by who is speaking loudest. A row with no source is a memory, and a timeline assembled during the review is a narrative. Export it while the incident runs, from the systems that saw it happen.

### No owner

An unowned action never closes. The tracker needs a name and a date at the moment the action is written, and a duplicate points at its original instead of living beside it.

### The pattern

Each failure is cheap to prevent at the time and impossible to repair afterwards. The review does not need better tools; it needs these four steps to happen in order, while the evidence is still warm.

> **The honest caveat:** a perfect bundle does not prove the incident was handled well, only that it can be examined.

> **The lesson:** evidence fails in the gaps between steps, not in the tools.

## In one line

> **Evidence fails in the gaps.** Four steps skipped, four questions you cannot answer.

**Hash the copy**

```bash
sha256sum auth.log > auth.log.sha256
```
