---
id: p105
title: "6 numbers every sysadmin should know"
slug: 6-numbers-every-sysadmin-should-know
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, DevOps, ITInfrastructure, CommandLine]
source: "LinkedIn post P105 · Linux + IT series"
linkedin_date: 2027-05-30
design: numbers
---

# 6 numbers every sysadmin should know

Six numbers that keep coming up in Linux and server work. Each one explains a whole category of problems.

## Quick reference

| Number | What | Why it matters |
|:--|:--|:--|
| **0** | Exit code for success | Anything else means an error. Check it with `echo $?`. |
| **1** | PID of the init system | systemd is process 1. Everything else starts from it. |
| **1024** | Privileged port limit | Ports below 1024 need root, or a capability, to bind. |
| **255** | Highest exit code | Exit codes run from 0 to 255. exit 256 becomes 0. |
| **8.76 h** | Downtime a year at 99.9% | Three nines still allows almost nine hours of outage. |
| **127.0.0.1** | Loopback address | Traffic that never leaves the machine. Bind internal services here. |

## Explained

- **0** — the exit code for success. Every command returns a number when it finishes. Zero means it worked, anything else is an error. `echo $?` shows the last one, and it is what && and || in scripts and cron monitoring are checking.

- **1** — the process ID of the init system. On modern Linux that is systemd. It starts every other service and adopts orphaned processes. That is why ps shows PID 1 on every Linux system, and why a container's main process runs as PID 1 inside its own namespace.

- **1024** — the privileged port limit. Ports below 1024, like 22, 80 and 443, need root or the CAP_NET_BIND_SERVICE capability to bind. This is why web servers start as root and then drop privileges, or sit behind a proxy.

- **255** — the highest exit code. Exit codes are stored in 8 bits, so they run from 0 to 255. A script that does exit 256 actually returns 0, success. Codes above 128 usually mean the process was killed by a signal: 137 is 128 + 9, SIGKILL, often the OOM killer.

- **8.76 hours** — the downtime per year that 99.9% availability still allows. Three nines sounds strict. It is almost nine hours of outage a year, or about 43 minutes a month.

- **127.0.0.1** — the loopback address. Traffic to it never leaves the machine. Databases, caches and admin panels that only local apps use should listen here, not on 0.0.0.0.

## In one line

> **Numbers make things concrete.** Know these and many error messages explain themselves.

**Check the last exit code**

```bash
echo $?
```
