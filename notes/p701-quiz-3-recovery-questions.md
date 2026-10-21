---
id: p701
title: "Quiz: 3 recovery questions"
slug: quiz-3-recovery-questions
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, CyberSecurity, SRE, Backup, Quiz]
source: "LinkedIn post P701 · IR series"
linkedin_date: 2031-03-20
design: quiz
---

# Quiz: 3 recovery questions

Three questions about the last mile of an incident: the order you rotate in, the certificate you share, and the restore point you bet the recovery on. Answer before the reveal.

## Quick reference

**Q1. Why does a credential rotation have an order?**

- a) Alphabetical order is easier to audit
- b) Dependents move after their dependencies
- c) The vault requires a fixed order

> **Answer:** b) Dependents move after their dependencies. A consumer that still holds the old value fails when its dependency rotates. Rotate the dependency, verify each consumer, then retire the old value.

**Q2. Why does a shared certificate change the replacement plan?**

- a) It always expires sooner
- b) Every host holds the file before any reload
- c) It needs a new serial number

> **Answer:** b) Every host holds the file before any reload. One reload can serve the new serial while the other hosts still serve the old. Replace everywhere, then reload one host at a time and check the serial from outside.

**Q3. What must a restore point prove before you use it?**

- a) That it is the newest snapshot
- b) That it is complete, pre-incident and restored
- c) That it is stored in another region

> **Answer:** b) That it is complete, pre-incident and restored. A catalog entry is a claim. The point must be complete, taken before the incident, and drilled at least once; an untested backup is a gamble.

## Explained

### Question one

Why does a credential rotation have an order? Because the registry is alphabetical? No. A consumer that still holds the old value fails the moment its dependency rotates. The dependency goes first, the consumer is verified against the new value, and only then is the old value retired. Skip that order and the outage looks like a new incident.

### Question two

Why does a shared certificate change the replacement plan? Because it expires sooner? No. One reload can start serving the new serial while the other hosts still serve the old. Replace the file everywhere, then reload one host at a time and check the serial from outside. The second host is not a backup; it is a second place the same change must be verified.

### Question three

What must a restore point prove before you use it? That it is the newest? No. It must be complete, taken before the incident, and restored at least once. A catalog entry is a claim; a drilled restore is evidence. A snapshot nobody has restored is a backup, not a recovery plan.

> **The honest caveat:** passing this quiz tests the plan, not your incident.

> **The lesson:** recovery is a sequence, not a checklist. If you got these, you are already treating it that way.

## In one line

> **Order, group, prove.** Three answers that keep a recovery in sequence.

**Run the plan**

```bash
python3 restore_point.py cat.json
```
