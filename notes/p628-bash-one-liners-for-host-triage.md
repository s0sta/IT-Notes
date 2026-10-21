---
id: p628
title: "Bash one-liners for host triage"
slug: bash-one-liners-for-host-triage
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Linux, CommandLine, SysAdmin, SRE]
source: "LinkedIn post P628 · ShellSec series"
linkedin_date: 2030-10-01
design: cheatsheet
---

# Bash one-liners for host triage

A host checkup needs a handful of one-liners you can type from memory, and the judgement to read them in the right order.

## Quick reference

### Disk

```bash
df -hP | awk '$5+0 > 80'
df -i | awk '$5+0 > 80'
du -xsh /var/* | sort -h | tail
find /var/log -type f -size +1G
lsof +L1 2>/dev/null | head
```

### Memory

```bash
free -m
grep MemAvailable /proc/meminfo
ps -eo rss,comm --sort=-rss | head
dmesg | grep -i 'killed process'
cat /proc/pressure/memory
```

### Processes

```bash
ps -eo stat,pid,comm | grep ^Z
ps -eo pcpu,pid,comm --sort=-pcpu | head
ps -eo nlwp,pid,comm --sort=-nlwp | head
lsof -p <pid> | wc -l
cat /proc/loadavg
```

### Network

```bash
ss -lntup
ss -s
ss -tan state established | wc -l
ip -br addr
ss -lntp | grep 0.0.0.0
```

## Explained

### Disk

`df -hP` shows the filesystem and `df -i` shows the inodes. `du -xsh /var/*` finds the directory that grew, `find -size +1G` lists the biggest logs, and `lsof +L1` finds a deleted file still holding its blocks.

### Memory

`free -m` gives the summary, but available is the number that matters, not free. The RSS sort names the biggest resident process, `/proc/pressure/memory` shows tasks stalled, and `dmesg | grep -i 'killed process'` says what the kernel killed. PSI needs kernel 4.20 or newer.

### Processes

`ps -eo stat,pid,comm | grep ^Z` finds zombies, which are a bug in the parent. The two sort lines find the process eating CPU and the one with the most threads. `lsof -p <pid>` counts one process's descriptors, and `cat /proc/loadavg` gives load without parsing uptime.

### Network

`ss -lntup` lists listeners with their process, and `ss -s` gives the summary. The established count is the load you serve, `ip -br addr` shows the addresses, and grep 0.0.0.0 finds a service that meant to stay local.

### The habit

Run them in that order: disk, memory, processes, network. Each answer changes which question you ask next.

> **The honest caveat:** ss and lsof need privileges to see other users' processes, so a hardened host may show ? instead of a name.

> **The lesson:** know the command before you need it, because at 3 a.m. you will not learn it.

## In one line

> **Twenty commands, one host.** Five per area beats fifty you cannot recall under pressure.

**A first look**

```bash
uptime; df -h; free -h
```
