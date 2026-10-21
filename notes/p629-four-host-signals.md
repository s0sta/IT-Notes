---
id: p629
title: "Four host signals"
slug: four-host-signals
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SRE, Observability, SysAdmin, Troubleshooting]
source: "LinkedIn post P629 · ShellSec series"
linkedin_date: 2030-10-03
design: explainer
---

# Four host signals

A slow host rarely has one cause. Four signals explain most of the pages I have answered, and each one is narrower than its name suggests.

## Quick reference

### Disk is full

- `df -h` shows bytes; `df -i` shows inodes
- A deleted file holds space until its fd closes
- `du -x --max-depth=1 /var` finds the growth
- Alert at 80%, not at 100%: at 100% you are down

### Memory pressure

- Available is the number, not free
- The OOM killer scores; it does not rank RSS
- PSI shows tasks stalled on memory
- MemoryMax caps one service, not the host

### Load average

- Load counts runnable plus uninterruptible tasks
- Compare load with nproc, never with 1.0
- High load and idle CPU means I/O wait
- A 4-core box at load 4 is saturated

### File descriptors

- Every socket and open file is a descriptor
- ulimit -n is per process, not per host
- `ls /proc/`\<pid>/fd counts one process
- Too many open files is a leak, not a limit

> **Note:** Load is a queue length, not a percentage. Read it beside nproc.

## Explained

### Disk

`df -h` measures bytes, `df -i` measures inodes, and a deleted file keeps both until its last descriptor closes. That is why du and df can disagree on a host with no free space. Alert at 80 per cent, because at 100 per cent writes fail and the cleanup is no longer controlled.

### Memory

Available is the number, not free. The kernel uses spare memory for cache and gives it back under pressure. The OOM killer scores processes instead of ranking them by RSS, so the largest process is not always the victim. Pressure stall information shows the tasks that are actually waiting.

### Load

Load counts runnable tasks plus tasks in uninterruptible sleep, usually disk I/O. On four cores, a load of 4 is saturated and a load of 8 is a queue. Read it beside CPU usage: high load with idle CPU means the disks, not the processor.

### File descriptors

Every socket and open file is a descriptor. ulimit -n is a per-process limit, not a host limit, so one service can hit it while the box looks idle. `ls /proc/`\<pid>/fd counts one process, and a rising count is a leak long before the error appears.

> **The honest caveat:** these four are the common signals, not the only ones; a host can pass all four and still drop packets.

> **The lesson:** read the signal behind the alarm, not the alarm itself.

## In one line

> **Read the signal, not the alarm.** One number rarely explains a slow host. Four usually do.

**Check all four**

```bash
uptime; free -m; df -h; df -i
```
