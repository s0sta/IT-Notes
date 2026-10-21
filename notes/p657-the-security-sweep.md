---
id: p657
title: "The security sweep"
slug: the-security-sweep
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, DevSecOps, CyberSecurity, Automation, SRE]
source: "LinkedIn post P657 · ShellSec series"
linkedin_date: 2030-12-08
design: architecture
---

# The security sweep

A security sweep is not a scanner. It is a loop: collect the evidence the host already has, match it against something you decided in advance, and act once.

## Quick reference

- **Tier 1 · Collect:** SUID, SGID and ACLs (FILES) · Auth and cron logs (LOGS) · Registry images (IMG)
- **Tier 2 · Match:** SUID baseline (BASE) · Secret patterns (RULE) · CVE allowlist (ALLOW) · Login policy (LOGIN)
- **Tier 3 · Act:** Patch or remove (FIX) · Rotate the secret (ROT) · Ticket and owner (TKT)

**Request flow:** SUID, SGID and ACLs → SUID baseline → Patch or remove; Auth and cron logs → Secret patterns → Rotate the secret; Auth and cron logs → Login policy → Patch or remove; Registry images → CVE allowlist → Ticket and owner

**Around it:** Cron or timer (CRON) · CI image gate (CI) · Ticket queue (TKT) · Audit trail (AUDIT)

## Explained

### Collect

Three sources cover most host regressions. The filesystem gives setuid and setgid bits and ACLs, the auth and cron logs give logins and secret-shaped lines, and the registry gives the image scan. Each source has a read-only script in this phase, and each one prints a line you can diff.

### Match

Four baselines turn evidence into a decision: the approved setuid set, the secret-name patterns, the CVE allowlist with owners, and the login policy of hours, root and failure counts. Matching is where a sweep earns its keep. Without a baseline, every finding is an opinion.

### Act

A new setuid file is removed or explained, a leaked secret is rotated, a privileged image is rebuilt or allowlisted with an expiry, and an unexpected login is blocked and reviewed. The ticket carries the owner, because the sweep will find the same thing tomorrow if nobody owns it.

Around the tiers, cron or a systemd timer starts the collect step, CI runs the image gate before deploy, the ticket queue receives the act step, and the audit trail keeps the evidence.

> **The honest caveat:** a sweep finds what you taught it to look for, so a new attack path needs a new check.

> **The lesson:** collect is cheap, match is the work, and act is the only tier that changes the risk.

## In one line

> **Collect, match, act.** Three tiers, one loop, and an owner for every finding.

**Start the sweep:** `suid_watch.sh --update /`
