---
id: p659
title: "Four security regressions"
slug: four-security-regressions
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, Linux, CyberSecurity, DevSecOps, SecOps]
source: "LinkedIn post P659 · ShellSec series"
linkedin_date: 2030-12-12
design: explainer
---

# Four security regressions

Four regressions cover most of the security tickets I see on Linux hosts, and each one has a shell check that fits in a cron line.

## Quick reference

### New SUID binary

- Mode 4755 and owned by root
- A package upgrade or an intruder
- A baseline turns it into a diff

### Leaked secret

- A password in `/etc/cron.d/db`
- Readable by the service account
- Mask the value, then rotate it

### Privileged image

- CRITICAL published after the build
- The base runs as root by default
- Gate HIGH and CRITICAL in CI

### Unexpected login

- Root at 02:14 from a new address
- Three failures, then a success
- last and lastb already know

> **Note:** A regression is a change you did not approve. The sweep is a diff, not a score.

## Explained

### New SUID binary

A package upgrade or an intruder drops a root-owned file with the setuid bit. Often 4755, it runs as root, and nothing in the deploy log mentions it. A baseline of the setuid set turns it into a diff, and the diff names the file.

### Leaked secret

A cron job needs a database password, so it lives in `/etc/cron.d/db` or a .env file next to the app. The file is readable by the service account, copied into a backup, and pasted into a ticket. A scan that masks the value finds the line without repeating the secret.

### Privileged image

The base image has a CRITICAL CVE that was published after the build, or the Dockerfile runs as root with a writable filesystem. A gate that fails on HIGH and CRITICAL, with an allowlist that has owners and expiry dates, keeps the exception visible.

### Unexpected login

Root at 02:14 from a new address, or three failures followed by a success. last and lastb already have the evidence; the check is what turns it into a finding.

> **The honest caveat:** a check only catches the regression you taught it, and an attacker who knows the sweep can avoid all four.

> **The lesson:** a regression is a change nobody approved, and a diff is how you see it.

## In one line

> **A change you did not approve.** Four regressions, four checks, one cron line each.

**Check one host:** `audit_logins.sh`
