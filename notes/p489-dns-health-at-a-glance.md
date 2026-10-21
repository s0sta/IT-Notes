---
id: p489
title: "DNS health at a glance"
slug: dns-health-at-a-glance
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, SRE, Observability, Networking, DevOps]
source: "LinkedIn post P489 · Network series"
linkedin_date: 2029-11-11
design: dashboard
---

# DNS health at a glance

Monday stand-up starts with a page about a site that is up for some users and gone for others. Six DNS numbers narrow the argument before anyone opens a laptop.

## Quick reference

**Status:** Production, last 24h

| Metric | Value | Note |
|:--|:--|:--|
| Resolution failures | **0.42%** | SERVFAIL and timeouts |
| Slow lookups | **2.1%** | over 200ms, p95 340ms |
| TTL coverage | **38%%** | records at 300s or less |
| Failing CAA | **2** | zones blocking the CA |
| Cert mismatch | **1** | name or chain, 7 days |
| Propagation | **11m** | median after a change |

## Explained

### The tiles

Resolution failures: 0.42 per cent of queries ended in SERVFAIL or a timeout in the last day.

Slow lookups: 2.1 per cent took over 200 milliseconds, with a p95 of 340ms.

TTL coverage: 38 per cent of records carry a TTL of 300 seconds or less, so only that share can move quickly in a failover.

Failing CAA: two zones have a CAA policy that blocks the certificate authority they use, which turns into a renewal failure later.

Cert mismatch: one certificate does not match its name or its chain, found in the last seven days.

Propagation: eleven minutes at the median between a record change and the new answer being seen.

### What it misses

The resolver only sees queries that reach it. A client on DNS over HTTPS, a browser with its own cache or a host with a stale `/etc/hosts` entry is invisible here. A resolver log can be sampled, too, so a rare failure can hide between two quiet minutes.

> **The honest caveat:** every tile is a snapshot, and a zero can mean no failures or no traffic; check the query count before you celebrate.

> **The lesson:** the dashboard starts the DNS review; it does not replace the lookup.

## In one line

> **DNS fails before HTTP.** Six numbers, and the one question they cannot answer.

**Check the ttl**

```bash
dig example.com +noall +answer
```
