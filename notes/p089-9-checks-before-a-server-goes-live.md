---
id: p89
title: "9 checks before a server goes live"
slug: 9-checks-before-a-server-goes-live
sections: [it, devsecops]
topic: "IT operations & incidents"
tags: [Linux, SysAdmin, DevOps, ITOperations, CyberSecurity]
source: "LinkedIn post P89 · Linux series"
linkedin_date: 2027-04-22
design: checklist
---

# 9 checks before a server goes live

The app works, the demo went well, and the server is about to go live. Nine checks first, because after today, real people depend on it.

## Quick reference

### Access

- **Named admin accounts** — no shared root logins
- **SSH keys, no passwords** — `PasswordAuthentication no`
- **Only needed ports open** — `ufw status verbose`

### Operations

- **Monitoring and alerts** — CPU, disk, memory, uptime
- **Backups and a restore** — a tested restore, not a job
- **Logs rotate** — `logrotate -d /etc/logrotate.conf`

### Basics

- **Time in sync** — `timedatectl`
- **Security updates automatic** — `apt install unattended-upgrades`
- **Written down** — owner, purpose, how to restart

## Explained

### Access

- **Named admin accounts** — every admin logs in as themselves and uses sudo. No shared root password, so you always know who did what.
- **SSH keys, no passwords** — `PasswordAuthentication no` in sshd_config, after key login is tested. Automated password guessing becomes useless.
- **Only needed ports open** — `ufw status verbose` should show the web ports and SSH, and nothing you cannot explain.

### Operations

- **Monitoring and alerts** — CPU, memory, disk space and an external uptime check, with alerts that reach a person. If it breaks at night, you hear about it before the users do.
- **Backups and a restore** — not just a backup job, but one restore you have actually tested on this server.
- **Logs rotate** — `logrotate -d /etc/logrotate.conf` is a dry run. Make sure the application logs are included, or the disk fills up in a few months.

### Basics

- **Time in sync** — `timedatectl` should say the clock is synchronized. Wrong time breaks TLS, tokens and every log timeline.
- **Security updates automatic** — `apt install unattended-upgrades` on Ubuntu or Debian, so security patches do not wait for someone to remember.
- **Written down** — who owns the server, what it does, how to restart it, and where the backups are. The person reading it at 3 AM may not be you.

Live is not the finish line. It is the moment someone else starts to depend on it.

## In one line

> **Live is not the finish line.** It is the moment someone else starts to depend on it.

**The 10-second audit**

```bash
ufw status; timedatectl; systemctl --failed
```
