---
id: p578
title: "First-response commands for a host incident"
slug: first-response-commands-for-a-host-incident
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SysAdmin, SRE, CommandLine, Troubleshooting]
source: "LinkedIn post P578 · PythonFixes series"
linkedin_date: 2030-06-06
design: cheatsheet
---

# First-response commands for a host incident

The page says the host is down. You have four minutes before the incident channel fills with theories, and twenty commands that answer the first questions. Four blocks, in this order.

## Quick reference

### Load

```bash
uptime
cat /proc/loadavg
nproc
vmstat 1 5
ps -eo stat | grep -c R
```

### Disk

```bash
df -h
df -i
du -xh --max-depth=1 / | sort -h
lsof +L1 | head
iostat -xz 1 3
```

### Memory

```bash
free -m
ps -eo rss,comm --sort=-rss | head
dmesg -T | grep -i 'killed process'
cat /proc/pressure/memory
slabtop -o | head
```

### Processes

```bash
ps -eo pid,ppid,stat,comm
ps -eo stat | grep -c Z
ps -eo pid,etime,cmd --sort=-etime
lsof -p 4242 | wc -l
ss -s
```

## Explained

### Load

`uptime` gives three load numbers. `cat /proc/loadavg` adds the running and total process counts, and nproc tells you how many cores that load is spread over. `vmstat 1 5` says whether the box is CPU-bound, IO-bound or swapping. `ps -eo stat | grep -c R` counts what is runnable.

### Disk

`df -h` for bytes and `df -i` for inodes, because a filesystem can be full either way. `du -xh --max-depth=1 / | sort -h` finds the directory that grew. `lsof +L1` finds deleted files still held open, which df counts and du cannot see. `iostat -xz 1 3` says whether the device is saturated.

### Memory

`free -m`, then `ps -eo rss,comm --sort=-rss | head` for the top consumers. `dmesg -T | grep -i 'killed process'` answers whether the kernel already acted. `cat /proc/pressure/memory` shows stall time, the number that predicts a page. slabtop -o | head catches kernel memory that no process owns.

### Processes

`ps -eo pid,ppid,stat,comm` names the state and the parent. `ps -eo stat | grep -c Z` counts zombies. `ps -eo pid,etime,cmd --sort=-etime` shows what has run longest. `lsof -p 4242 | wc -l` counts one process's descriptors; `ss -s` summarises every socket.

> **The honest caveat:** a snapshot is not a timeline. Run the same four blocks twice, a minute apart, and compare.

> **The lesson:** read before you restart, because a restart deletes the evidence.

## In one line

> **Look before you restart.** Four minutes of reading beats an hour of guessing.

**Start at load**

```bash
uptime
```
