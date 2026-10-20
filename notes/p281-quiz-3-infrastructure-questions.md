---
id: p281
title: "Quiz: 3 infrastructure questions"
slug: quiz-3-infrastructure-questions
sections: [it]
topic: "Networking & DNS"
tags: [ITInfrastructure, Networking, RAID, TCP, Quiz]
source: "LinkedIn post P281 · Visual series"
linkedin_date: 2028-07-13
design: quiz
---

# Quiz: 3 infrastructure questions

Three questions show up in almost every infrastructure interview, and the wrong answer is usually the one that sounds clever.

## Quick reference

**Q1. A RAID 5 array loses one drive. What is still true?**

- a) It survives: parity is spread
- b) It is gone: no parity here
- c) It survives with only two drives

> **Answer:** a) It survives: parity is spread. RAID 5 spreads parity across at least three drives and tolerates one failure; capacity is n-1. A second failure during the rebuild ends the set.

**Q2. How many /24 subnets fit inside one /16?**

- a) 16
- b) 256
- c) 65,536

> **Answer:** b) 256. A /16 holds 65,536 addresses and a /24 holds 256, so 65,536 / 256 = 256 subnets. Each extra prefix bit doubles the count.

**Q3. A live video call drops packets. Which transport fits?**

- a) TCP, because it re-sends loss
- b) UDP, because late data is useless
- c) Either; the port decides

> **Answer:** b) UDP, because late data is useless. Video needs low latency, and a re-sent frame arrives too late to show. UDP drops it and moves on; WebRTC uses UDP and adds a jitter buffer and congestion control.

## Explained

### Parity

Question one: a RAID 5 array loses one drive. It survives, because parity is striped across the set and the missing data is rebuilt from the remaining drives. RAID 5 needs at least three drives, gives the capacity of n-1, and tolerates exactly one failure. A second failure before the rebuild finishes ends the array.

### Prefixes

Question two: how many /24s fit in a /16? A /16 holds 65,536 addresses; a /24 holds 256, of which 254 are usable. Divide and the answer is 256 subnets, 65,536 addresses in total. Each extra prefix bit doubles the subnet count and halves the size.

### Transport

Question three: a live video call drops packets. UDP is the right default, because a re-sent frame arrives too late to show. TCP would hold the stream while it retransmits, which is worse for a call. WebRTC uses UDP, adds a jitter buffer and its own congestion control.

> **The honest caveat:** RAID 5's one-drive tolerance is a promise about drives, not about rebuild time; on large disks a rebuild can run for days, and RAID 6 or RAID 10 is often the safer answer.

> **The lesson:** the basics are not the beginner questions; they are the ones that decide the outage.

## In one line

> **The basics still catch the outage.** Parity, prefixes and ports explain most of the pager.

**Check the array**

```bash
mdadm --detail /dev/md0
```
