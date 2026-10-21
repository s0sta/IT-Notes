---
id: p580
title: "9 steps of a host incident"
slug: 9-steps-of-a-host-incident
sections: [it, devsecops]
topic: "IT operations & incidents"
tags: [SRE, IncidentResponse, Linux, DevOps, OnCall]
source: "LinkedIn post P580 · PythonFixes series"
linkedin_date: 2030-06-11
design: steps
---

# 9 steps of a host incident

The page arrives at 03:12 and the host is still up, which is the worst kind of incident: nothing is obviously broken and everything is slow. Nine steps, three groups, one order.

## Quick reference

### Assess — Name the tier in three commands

```bash
# Load, memory and bytes in one shot.
uptime; free -m; df -h
# Inodes and the kernel's last words.
df -i; dmesg -T | tail -40
# Sockets, states and dead children.
ss -s; ps -eo stat | grep -c Z
```

### Contain — Stop the damage, not the box

```bash
# Stop the loop before it fills the disk.
systemctl stop api.service
# Put a memory cap in before the restart.
systemctl edit api.service
# Drop the flood at the door.
iptables -I INPUT -s 10.0.3.17 -j DROP
```

### Fix — Change one thing, then prove it

```bash
# Restart with the new limit in place.
systemctl restart api.service
# Read the line before the first kill.
journalctl -u api --since 03:00
# Leave a check behind, not a note.
systemctl enable --now inode_watch.timer
```

## Explained

### Assess

The terminal runs the first three commands before you touch anything. `uptime; free -m; df -h` gives load, memory and bytes in one line. `df -i; dmesg -T | tail -40` adds inodes and the kernel's last words, which is where an OOM kill or a disk error appears first. `ss -s; ps -eo stat | grep -c Z` counts sockets, states and dead children. Under a minute, and you know which tier you are in.

### Contain

`systemctl stop api.service` stops the loop before it fills the disk. `systemctl edit api.service` puts a memory cap in place before the restart, so the next spike is contained by the cgroup rather than the kernel. `iptables -I INPUT -s 10.0.3.17 -j DROP` removes a flood at the door. Containment is temporary by design; it buys the fix, not the week.

### Fix

`systemctl restart api.service` brings the service back with the new limit. `journalctl -u api --since 03:00` reads the line before the first kill, which is the actual cause. `systemctl enable --now inode_watch.timer` leaves a check behind, so the same disk does not surprise the next on-call.

> **The honest caveat:** the restart in the contain step clears the evidence. Capture the logs before you stop anything.

> **The lesson:** assess, contain, fix, in that order, every time.

## In one line

> **Assess, contain, then fix.** Three groups, nine commands, one order that holds.

**Assess first**

```bash
uptime; df -h; df -i
```
