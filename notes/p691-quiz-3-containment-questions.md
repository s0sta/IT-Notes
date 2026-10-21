---
id: p691
title: "Quiz: 3 containment questions"
slug: quiz-3-containment-questions
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, CyberSecurity, SRE, DevOps, Quiz]
source: "LinkedIn post P691 · IR series"
linkedin_date: 2031-02-25
design: quiz
---

# Quiz: 3 containment questions

Phase two of this series is containment, and it ends with three questions. Nine posts of tools and posters came before it. Answer before the reveal.

## Quick reference

**Q1. Why keep a management path open when you quarantine a host?**

- a) So you can finish the fix without travelling
- b) Because firewalls need a default allow
- c) To keep the metrics agent reporting

> **Answer:** a) So you can finish the fix without travelling. The host you cannot reach is the host you cannot fix. The console is the last rule you remove, not the first one you cut.

**Q2. Why does dependency order matter when disabling an identity?**

- a) Cloud roles are slower to revoke than logins
- b) Alphabetical order is easier to audit
- c) The IdP session outlives a downstream lock

> **Answer:** c) The IdP session outlives a downstream lock. Kill the IdP session first, or the user signs back into every downstream system. Disable in tier order: IdP, cloud, source control, CI.

**Q3. Why does an allowlist beat a blocklist at the edge?**

- a) It is cheaper to store in the WAF
- b) It fails closed when a new address appears
- c) It blocks more traffic by default

> **Answer:** b) It fails closed when a new address appears. A blocklist only stops what you already know. An allowlist denies the address nobody has seen yet, which is the one the attacker uses next.

## Explained

### Question one

Why keep a management path open when you quarantine a host? Because the host you cannot reach is the host you cannot fix. The console is the last rule you remove, not the first one you cut. A management rule buried under a drop never fires. A quarantine that locks you out is an outage with a story.

### Question two

Why does dependency order matter when disabling an identity? Because the identity provider session outlives a downstream lock. Disable the IdP first, then cloud, source control and CI. Do it alphabetically and the user signs back into everything you just locked. A break-glass account is held, never disabled by a script.

### Question three

Why does an allowlist beat a blocklist at the edge? Because a blocklist only stops what you already know. An allowlist denies the address nobody has seen yet, which is the one the attacker will use next. The review cost is the control; the benefit is that failure is closed.

> **The honest caveat:** an allowlist is only as good as its review, and a stale allow is a blocklist with better marketing.

Phase two is done: five tools, ten posts, one order. Scope, cut, verify. If you missed one, reread P682 before the next incident.

## In one line

> **Contain by rule, not by memory.** Three answers, one habit: prove the path before you cut it.

**Replay the phase:** P682 to P690
