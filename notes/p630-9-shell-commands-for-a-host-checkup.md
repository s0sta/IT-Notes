---
id: p630
title: "9 shell commands for a host checkup"
slug: 9-shell-commands-for-a-host-checkup
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Linux, CommandLine, SRE, SysAdmin]
source: "LinkedIn post P630 · ShellSec series"
linkedin_date: 2030-10-06
design: terminal
---

# 9 shell commands for a host checkup

A host checkup is nine commands in three passes. Look at the whole box, measure the one thing that hurts, then act once and write down what you changed.

## Quick reference

### Look at the whole host

```bash
# 8 cores, load 9.4: saturated
uptime
# bytes left before inodes
df -h /
# inodes are the wall here
df -i /
```

### Measure the one thing that hurts

```bash
# available is what matters
free -m
# one process owns the box
ps -eo pcpu,pid,comm --sort=-pcpu | head -3
# sockets, not ports
ss -s
```

### Act once, and note the time

```bash
# read before the restart
journalctl -u api --since '15 min ago'
# rotate first, delete never
logrotate -f /etc/logrotate.d/app
# last resort, one unit
systemctl restart api
```

## Explained

### Look

`uptime` gives the load and the age of the boot. `df -h` gives the bytes, and `df -i` gives the inodes; on a container host the second one is usually the surprise. Stop when one number explains the page.

### Measure

`free -m` separates cache from available. The process sort shows the one process that owns the CPU, not the top ten. `ss -s` counts the sockets, which is the number that often grows before a file descriptor limit does.

### Act

Read the journal before the restart, because the failure you are about to clear is the evidence you will want at noon. Rotate a log before you delete it. Restart one unit, not the host: the restart buys an hour, and the journal buys the fix.

### The habit

Look, measure, act, in that order. The order is the discipline: it stops you from restarting a host because one column in top looked red.

> **The honest caveat:** restart and logrotate change the system, so run them one at a time and note the time in the incident channel.

> **The lesson:** nine commands and one order beat a dashboard you cannot read under pressure.

## In one line

> **Look, measure, then act.** Nine commands, one order, no guessing.

**Try it**

```bash
df -h; df -i; free -m
```
