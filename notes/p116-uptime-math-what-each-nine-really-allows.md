---
id: p116
title: "Uptime math: what each nine really allows"
slug: uptime-math-what-each-nine-really-allows
sections: [it, devsecops]
topic: "Observability & SRE"
tags: [SRE, ITInfrastructure, CloudComputing, DevOps, ITManagement]
source: "LinkedIn post P116 · Linux + IT series"
linkedin_date: 2027-06-24
design: numbers
---

# Uptime math: what each nine really allows

We need 99.99% uptime. Before agreeing, it helps to know what that number actually allows. One year has 525,600 minutes.

## Quick reference

| Number | What | Why it matters |
|:--|:--|:--|
| **99%** | 3.65 days a year | Two nines. Fine for internal tools, not for a shop. |
| **99.9%** | 8.76 hours a year | Three nines. About 43 minutes of downtime a month. |
| **99.95%** | 4.38 hours a year | A common cloud SLA for a single service. |
| **99.99%** | 52.6 minutes a year | Four nines. Needs redundancy and automatic failover. |
| **99.999%** | 5.26 minutes a year | Five nines. One bad deploy uses up the whole year. |
| **43.8 min** | A month at 99.9% | That includes maintenance, unless the SLA excludes it. |

## Explained

99% is 3.65 days of downtime a year. Two nines sounds high, but it allows a whole long weekend of outage. Acceptable for an internal tool, painful for an online shop.

99.9% is 8.76 hours a year, or about 43 minutes a month. Three nines is a realistic target for a well-run single server with good monitoring and backups.

99.95% is 4.38 hours a year. A common SLA for a single cloud service or VM. Check whether it covers one instance or only a group across zones.

99.99% is 52.6 minutes a year. Four nines usually means no single points of failure: two or more servers, a load balancer, a replicated database, and failover that happens automatically, because a human cannot respond fast enough.

99.999% is 5.26 minutes a year. Five nines is a telecom and banking target. One bad deploy or one slow failover can use up the entire year's budget.

43.8 minutes is a month at 99.9%. Read the SLA carefully: does planned maintenance count? Is it measured per month or per year? Does a slow site count as down?

The practical lesson: every extra nine roughly multiplies the cost and complexity. The right question is not how many nines can we get, but what does an hour of downtime actually cost us.

downtime = (1 - uptime) x 525,600 minutes.

## In one line

> **Every nine costs ten times more.** Pick the target the business needs, then build for it.

**The formula:** downtime = (1 - uptime) x 525,600 minutes
