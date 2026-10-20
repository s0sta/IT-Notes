---
id: p135
title: "What a healthy Linux server looks like"
slug: what-a-healthy-linux-server-looks-like
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SysAdmin, Monitoring, DevOps, Observability]
source: "LinkedIn post P135 · IT series"
linkedin_date: 2027-08-08
design: dashboard
---

# What a healthy Linux server looks like

When someone asks "is the server OK?", the useful answer is numbers, not a feeling. Here is what a healthy Linux box looks like, and why each number matters.

## Quick reference

**Status:** All systems normal

| Metric | Value | Note |
|:--|:--|:--|
| CPU | **34%** | 4 cores, load 1.3 |
| Memory | **61%** | 4.7 of 7.7 GiB used |
| Disk / | **48%** | 19 of 40 GB used |
| Swap | **4%** | Barely touched. Good. |
| Uptime | **87d** | since last reboot |
| Failed units | **0** | `systemctl --failed` |

## Explained

CPU at 34%, load 1.3 on 4 cores. The load average matters more than the percentage. On 4 cores, a load under 4 means no task is waiting for CPU. If load climbs well above the core count while CPU sits low, tasks are waiting on disk or network, not compute.

Memory at 61%, 4.7 of 7.7 GiB. Read the available figure, not free. Linux uses spare RAM as cache and hands it back when needed, so low free is normal and healthy. Low available is the real warning.

Disk at 48%. The number to watch is the trend, not the value. A disk at 48% that grows 1% a day gives you weeks of warning. Alert at 80%, not 100%, because a full disk breaks logging, databases and uploads at once.

Swap barely touched. A little swap use is fine. Heavy, constant swapping means the server is short on RAM and everything slows down.

Uptime 87 days. Useful context, but very long uptime also hints a kernel update and reboot are overdue.

Failed units: 0. `systemctl --failed` should be empty. One failed unit is the thread to pull before it becomes an outage.

The point of knowing the normal numbers is simple: when something spikes, you notice immediately instead of guessing.

Healthy is boring, and boring is the goal.

## In one line

> **Healthy is boring.** Know your baseline, and problems announce themselves.

**One-line snapshot**

```bash
uptime; free -h; df -h
```
