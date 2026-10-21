---
id: p690
title: "9 commands to contain a host"
slug: 9-commands-to-contain-a-host
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, Linux, SRE, CyberSecurity, CommandLine]
source: "LinkedIn post P690 · IR series"
linkedin_date: 2031-02-23
design: terminal
---

# 9 commands to contain a host

A host is contained when three things are true: the paths are cut, the process is understood, and the console still answers.

## Quick reference

### Cut the paths

```bash
# what still answers on the host
ss -tlnp
# database subnet, console kept
iptables -I INPUT -s 10.20.5.0/24 -j DROP
# stop the app, not the kernel
systemctl stop app.service
```

### Check the process

```bash
# parent chain, reparented to 1
ps -eo pid,ppid,stat,cmd | head
# open files: one number
lsof -p 412 | wc -l
# the last ten minutes
journalctl -u app --since -10m
```

### Keep the console

```bash
# prove the console first
ssh -o ConnectTimeout=5 ops@10.20.4.11
# management rule is first
nft list chain inet fw input
# timestamp the containment
date -u
```

## Explained

### Cut

`ss -tlnp` shows what is still listening; a service you did not expect is the first finding, and a listener you cannot name is a listener you have not contained. `iptables -I INPUT -s 10.20.5.0/24 -j DROP` drops traffic from the database subnet while the management subnet stays out of the rule. `systemctl stop app.service` stops the application without stopping the kernel, which keeps the host and its logs up.

### Check

`ps -eo pid,ppid,stat,cmd | head` shows the parent chain, and a process reparented to 1 has outlived its supervisor. `lsof -p 412 | wc -l` gives one number for open files; a jump from 200 to 2,000 is a leak or a download. Write the pid down; it is the handle for everything else. `journalctl -u app --since -10m` is the last ten minutes, which is usually the whole incident.

### Keep

`ssh -o ConnectTimeout=5 ops@10.20.4.11` proves the console, and you run it before the first cut. `nft list chain inet fw input` shows the management accept sitting above the drop. `date -u` timestamps the containment for the timeline you will write later.

> **The honest caveat:** rescue.target stops everything, including the agent you need; use it on a host you can reach through a console.

> **The lesson:** cut the path, keep the console, and write down the time.

## In one line

> **Cut the path, keep the console.** Nine commands, one rule: the cut never includes the way in.

**Try it**

```bash
ssh -o ConnectTimeout=5 ops@10.20.4.11
```
