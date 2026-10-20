---
id: p88
title: "9 commands to know any server in 60 seconds"
slug: 9-commands-to-know-any-server-in-60-seconds
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, ITSupport, DevOps, CommandLine]
source: "LinkedIn post P88 · Linux series"
linkedin_date: 2027-04-20
design: terminal
---

# 9 commands to know any server in 60 seconds

A new job, a new client, or a server nobody documented. Before you change anything, spend sixty seconds finding out what it is. Nine commands.

## Quick reference

### What is this machine?

```bash
# name, OS, kernel, VM or bare metal
hostnamectl
# the kernel that is running right now
uname -r
# time since the last reboot, and the load
uptime
```

### What does it run on?

```bash
# CPU model and number of cores
lscpu | grep -E 'Model name|^CPU\(s\)'
# memory. Read the available column
free -h
# disks, partitions and where they are mounted
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT
```

### What does it actually do?

```bash
# every service that is running
systemctl list-units --type=service --state=running
# what listens on which port
ss -tlnp
# what runs on a schedule
crontab -l; ls /etc/cron.d
```

## Explained

### What is this machine?

- `hostnamectl` — the host name, operating system, kernel, and whether it is a virtual machine or bare metal. One command, a lot of answers.
- `uname -r` — the kernel that is actually running. Compare it with the installed kernels to see if a reboot is overdue.
- `uptime` — how long since the last reboot, and the load average for the last 1, 5 and 15 minutes. 400 days of `uptime` also tells you something about patching.

### What does it run on?

- `lscpu | grep -E 'Model name|^CPU\(s\)'` — the CPU model and number of cores. Now the load average has context: a load of 4 is busy on 4 cores and quiet on 32.
- `free -h` — total memory and, more importantly, the available column. Low "free" is normal on Linux. Low "available" is not.
- `lsblk -o NAME,SIZE,TYPE,MOUNTPOINT` — the disks, their partitions, and where each one is mounted. Spot the data disk, LVM or RAID at a glance.

### What does it actually do?

- `systemctl list-units --type=service --state=running` — every running service. This is the real job description of the server.
- `ss -tlnp` — what is listening on which port, and which process owns it. Run with sudo to see the process names.
- `crontab -l; ls /etc/cron.d` — what runs on a schedule. Check other users' crontabs and systemctl list-timers too. Hidden jobs are where surprises come from.

## In one line

> **Understand it before you change it.** Sixty seconds of looking saves a day of guessing.

**Try it**

```bash
hostnamectl; uptime; ss -tlnp
```
