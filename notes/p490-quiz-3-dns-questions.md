---
id: p490
title: "Quiz: 3 DNS questions"
slug: quiz-3-dns-questions
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, Networking, SRE, DevOps, CloudNative]
source: "LinkedIn post P490 · Network series"
linkedin_date: 2029-11-13
design: quiz
---

# Quiz: 3 DNS questions

Three DNS questions come up in every incident review, and the answers are shorter than the arguments. Answer before the reveal.

## Quick reference

**Q1. Why can a CNAME not sit at the zone apex?**

- a) CNAMEs are only for subdomains
- b) SOA and NS already own that name
- c) The apex has no TTL

> **Answer:** b) SOA and NS already own that name. A CNAME must be the only data record at its name, and the apex must carry SOA and NS. Providers offer ALIAS or ANAME to map the apex.

**Q2. Why lower a record's TTL before a migration?**

- a) So the new record propagates instantly
- b) So resolvers skip the root servers
- c) So old cached answers expire sooner

> **Answer:** c) So old cached answers expire sooner. Caches keep the old record for its old TTL. Lower it at least one old TTL before the change, then raise it after the cutover.

**Q3. What does SERVFAIL usually mean?**

- a) The name does not exist
- b) The resolver could not get a valid answer
- c) The record has no TTL

> **Answer:** b) The resolver could not get a valid answer. An upstream timeout, a broken delegation or a failed DNSSEC check. NXDOMAIN is the name-does-not-exist answer; SERVFAIL says try again.

## Explained

### The apex

Why can a CNAME not sit at the zone apex? Because a CNAME must be the only data record at its name, and the apex must carry SOA and NS. Providers offer ALIAS, ANAME or CNAME flattening, which return an address at the apex without a real CNAME.

### The timer

Why lower a record's TTL before a migration? Because caches keep the old answer for its old TTL. Lower it at least one old TTL before the change, wait, then move the record and raise the TTL after the cutover.

### The failure

What does SERVFAIL usually mean? That the resolver could not get a valid answer: an upstream timeout, a broken delegation or a failed DNSSEC validation. It also appears when the authoritative servers disagree or one of them is lame. NXDOMAIN is the name-does-not-exist answer, and the two send you to different places.

> **The honest caveat:** CNAME flattening looks like a CNAME at the apex in a dashboard, but the provider is synthesising an A or AAAA answer; and a low TTL does not override a resolver's minimum or a client's own cache.

> **The lesson:** the record, the cache and the response code answer three different questions.

## In one line

> **Check the answer, not the rumour.** Three answers that turn a failed lookup into a next step.

**Ask the resolver**

```bash
dig example.com +comments
```
