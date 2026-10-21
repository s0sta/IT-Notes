---
id: p711
title: "Quiz: 3 evidence questions"
slug: quiz-3-evidence-questions
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, DFIR, CyberSecurity, SRE, Postmortem]
source: "LinkedIn post P711 · IR series"
linkedin_date: 2031-04-13
design: quiz
---

# Quiz: 3 evidence questions

The last post of the evidence phase, and the right place to stop: the hour after the fix, when the review asks what you can prove. Three questions. Answer before the reveal.

## Quick reference

**Q1. Why does a SHA-256 hash matter more than a copy of the file?**

- a) It compresses the evidence
- b) It proves the bytes have not changed
- c) It encrypts the contents

> **Answer:** b) It proves the bytes have not changed. A copy can be edited and still look identical. The digest changes with one byte, so it is the only cheap proof that what you kept is what you collected.

**Q2. What must every status update contain, whatever the phase?**

- a) A root cause and a fix date
- b) An impact and a next update time
- c) A named engineer and a ticket

> **Answer:** b) An impact and a next update time. The impact says who is affected; the next time says when you speak again. A root cause and a fix date are guesses early on, and a page built on guesses ages fast.

**Q3. Why is notification latency an incident metric?**

- a) It measures how fast the pager fires
- b) It measures time exposed without knowing
- c) It measures the size of the on-call rota

> **Answer:** b) It measures time exposed without knowing. Every minute before a stakeholder is told is a minute they cannot act: legal cannot issue the statement, support cannot answer the queue.

## Explained

### Question one

Why does a hash matter more than a copy? Because a copy can be edited and still look identical, while one changed byte changes the digest. SHA-256 is the cheap proof that the file you kept is the file you collected, and it is the first thing a reviewer asks for. A copy without a digest is a claim.

### Question two

What must every status update contain, whatever the phase? An impact and a next update time. The impact says who is affected; the next time says when you will speak again. A root cause and a fix date are guesses in the first hour, and a page built on guesses ages badly, which is how a status page loses its audience.

### Question three

Why is notification latency an incident metric? Because every minute before a stakeholder is told is a minute they cannot act. Legal cannot hold the statement, support cannot answer the queue, and the first version of the story comes from someone outside the incident. The gap is part of the damage.

> **The honest caveat:** knowing these three does not produce the evidence; somebody has to run the commands while the host is still up.

If you answered all three, you already treat communication as part of the incident.

## In one line

> **Evidence is a habit, not a tool.** Five tools, one rule: collect, hash, say it, and keep the list.

**Start the habit**

```bash
python3 evidence_collect.py /cases/inc-214
```
