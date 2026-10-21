---
id: p637
title: "The config and crypto sweep"
slug: the-config-and-crypto-sweep
sections: [it, devsecops]
topic: "Security & hardening"
tags: [DevSecOps, Linux, Bash, CyberSecurity, SRE]
source: "LinkedIn post P637 · ShellSec series"
linkedin_date: 2030-10-22
design: architecture
---

# The config and crypto sweep

A config and crypto sweep is three tiers, and most teams start at the third. They open a ticket, change a file, and never learn what the host looked like before the change.

## Quick reference

- **Baseline:** File hashes (HASH) · Authorised keys (KEY) · Certificate store (CERT)
- **Compare:** Drift check (DRIFT) · Key audit (AUDIT) · Expiry window (DAYS)
- **Report:** Fix list (FIX) · Ticket (TKT)

**Request flow:** File hashes → Drift check → Fix list → Ticket; Authorised keys → Key audit → Fix list; Certificate store → Expiry window → Ticket

**Around it:** Exit code (EXIT) · Cron (CRON) · Baseline store (BASE) · Runbook (RUN)

## Explained

### Baseline

The first tier is a read-only record. File hashes answer what the bytes were. Authorised keys answer who could log in. The certificate store answers what will expire. Take it at a known-good moment, store it off the host, and never let the check write into the tree it watches. A hash without a date is a fact without a context.

### Compare

The second tier is the diff. Drift compares hashes with the baseline. The key audit compares authorized_keys with policy. The expiry window compares notAfter with today. None of them changes a file, and each returns an exit code: 0 clean, 1 finding, 2 the check itself broke.

### Report

The third tier is the only one that writes. A fix list names the file, the owner and the command. A ticket carries the same facts into the queue. A report that says "config drift" without a path is a rumour with a timestamp.

> **The honest caveat:** a baseline is a claim about a moment. If the host was already compromised when you took it, you have baselined the compromise.

> **The lesson:** hash first, compare second, decide last.

## In one line

> **Hash first, then compare.** A baseline you cannot trust makes every later tier a guess.

**Start at the hash**

```bash
sha256sum /etc/ssh/sshd_config
```
