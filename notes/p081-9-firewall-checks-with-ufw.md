---
id: p81
title: "9 firewall checks with ufw"
slug: 9-firewall-checks-with-ufw
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Linux, Firewall, CyberSecurity, SysAdmin, Ubuntu]
source: "LinkedIn post P81 · Linux series"
linkedin_date: 2027-04-04
design: checklist
---

# 9 firewall checks with ufw

ufw makes the Linux firewall simple. Simple is not the same as safe. Nine checks for a firewall you can trust.

## Quick reference

### Before you enable

```bash
# Allow SSH first
ufw allow OpenSSH
# Deny incoming by default
ufw default deny incoming
# Allow outgoing by default
ufw default allow outgoing
```

### Open only what is needed

```bash
# Web ports only
ufw allow 80,443/tcp
# DB for the app only
ufw allow from 10.0.0.5 to any port 5432
# Rate-limit SSH
ufw limit OpenSSH
```

### Verify

```bash
# Rules look right
ufw status numbered
# Logging is on
ufw logging on
# Test from outside
nc -zv 203.0.113.10 5432
```

## Explained

### Before you enable

- `ufw allow OpenSSH` — first, always. Enable the firewall without this rule on a remote server and you have locked yourself out.
- `ufw default deny incoming` — nothing comes in unless a rule allows it. This is the whole point of a firewall.
- `ufw default allow outgoing` — the server can still reach updates, DNS and APIs. Tighten this later if you need to.

### Open only what is needed

- `ufw allow 80,443/tcp` — a web server needs these two ports, and nothing else from the internet.
- `ufw allow from 10.0.0.5 to any port 5432` — the database only accepts connections from the app server's IP. The rest of the world never sees it.
- `ufw limit OpenSSH` — blocks an IP that opens too many SSH connections in a short time. A simple brake on brute-force attempts.

### Verify

- `ufw status numbered` — read every rule. Numbers make it easy to delete the wrong one with ufw delete 3.
- `ufw logging on` — blocked connections are logged, so you can see what is knocking.
- `nc -zv 203.0.113.10 5432` — test from another machine. A rule only counts when you have confirmed it from the outside.

> **One honest caveat:** Docker writes its own iptables rules, and published container ports can bypass ufw completely. If you run Docker, check your exposed ports from outside, not just ufw status.

## In one line

> **Allow SSH before you enable.** Order matters. The firewall does exactly what you tell it.

**The safe start**

```bash
ufw allow OpenSSH && ufw enable
```
