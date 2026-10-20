---
id: p73
title: "9 checks after every Linux reboot"
slug: 9-checks-after-every-linux-reboot
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, ITOperations, DevOps, Troubleshooting]
source: "LinkedIn post P73 · Linux series"
linkedin_date: 2027-03-16
design: checklist
---

# 9 checks after every Linux reboot

A reboot that "worked" and a server that works are not the same thing. Nine checks to run every time a Linux server comes back up.

## Quick reference

### The system

```bash
# Nothing failed
systemctl --failed
# Booted the right kernel
uname -r
# Every disk is mounted
df -h
```

### The network

```bash
# IP and route look right
ip -br a; ip r
# Services are listening
ss -tlnp
# Clock is in sync
timedatectl
```

### The workload

```bash
# No new errors
journalctl -p err -b
# The app answers
curl -sI localhost
# Scheduled jobs still there
systemctl list-timers
```

## Explained

### The system

- `systemctl --failed` — any unit that did not start. An empty list is what you want to see.
- `uname -r` — the kernel that is actually running. After a kernel update, this confirms the new one booted, not the old one.
- `df -h` — every filesystem you expect is mounted. A data disk that did not mount means your app may be writing into an empty folder on the root disk.

### The network

- `ip -br a; ip r` — the right IP addresses on the right interfaces, and a default route. Short output, easy to read.
- `ss -tlnp` — the services that should be listening are listening, on the ports you expect.
- `timedatectl` — "System clock synchronized: yes". A wrong clock breaks TLS, logs and anything with tokens.

### The workload

- `journalctl -p err -b` — errors since this boot only. New errors after a reboot deserve a look before anyone reports them.
- `curl -sI localhost` — the app actually answers, not just the process running. Use your real health endpoint if you have one.
- `systemctl list-timers` — backups and scheduled jobs are still there and have a next run time.

This takes about five minutes. The alternative is finding out from a user, or from a backup that silently did not run.

Reboot is not the last step. Checking is.

## In one line

> **Reboot is not the last step.** Checking is. Five minutes now saves a long night later.

**A one-line first look**

```bash
systemctl --failed; df -h; journalctl -p err -b
```
