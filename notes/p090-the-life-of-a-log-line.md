---
id: p90
title: "The life of a log line"
slug: the-life-of-a-log-line
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, Logging, SysAdmin, CyberSecurity, DevOps]
source: "LinkedIn post P90 · Linux series"
linkedin_date: 2027-04-25
design: pipeline
---

# The life of a log line

Every log line on a Linux server has a life: it is written, collected, stored, rotated, maybe shipped, and eventually deleted. Knowing the path tells you where to look, and how long you have.

## Quick reference

1. **The app writes it** — To stdout, to a file, or to the syslog socket. · `logger`
2. **journald collects it** — systemd captures the output of every service. · `journalctl -u`
3. **rsyslog files it** — Gets a copy from the journal and writes classic log files. · `/var/log/syslog`
4. **logrotate rotates it** — Daily or by size: rename, compress, start a fresh file. · `app.log.1.gz`
5. **Shipped off the box** — Optional: sent to a central log server or SIEM. · `@@siem:514`
6. **Retention deletes it** — After N rotations, the oldest file is removed. · *rotate 14*

## Explained

1. **The app writes it.** To standard output, to its own file in `/var/log`, or to the syslog socket. logger "test" writes a line yourself, which is a handy way to test the whole chain.

2. **journald collects it.** For every service started by systemd, its output goes into the journal. `journalctl -u nginx` shows one service, `journalctl -b` the current boot. By default the journal may live only in memory and vanish at reboot unless `/var/log/journal` exists or Storage=persistent is set.

3. **rsyslog files it.** On Debian and Ubuntu, rsyslog receives the messages and writes the classic text files like `/var/log/syslog` and `/var/log/auth.log`. On RHEL-based systems, the equivalents are `/var/log/messages` and `/var/log/secure`.

4. **logrotate rotates it.** Usually daily, or when a file reaches a size limit, the current log is renamed to `app.log`.1, older ones are compressed to .gz, and a fresh file starts.

5. **Shipped off the box.** Optionally, rsyslog forwards everything to a central server or SIEM, for example \*.\* @@siem:514 over TCP. If an attacker cleans the local logs, the central copy survives.

6. **Retention deletes it.** With rotate 14, the fifteenth oldest file is deleted. That number decides how far back you can investigate.

The practical question to answer today: if an incident started three weeks ago, would your logs still be there?

## In one line

> **Know where logs go, and when they go away.** During an incident, a deleted log is a missing witness.

**See one line travel**

```bash
logger "test from $(hostname)" && journalctl -n 1
```
