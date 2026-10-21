---
id: p668
title: "Cron and systemd automation commands"
slug: cron-and-systemd-automation-commands
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Cron, Systemd, Linux, Automation]
source: "LinkedIn post P668 · ShellSec series"
linkedin_date: 2031-01-02
design: cheatsheet
---

# Cron and systemd automation commands

The crontab has one line and it has been there since 2023. These are the commands that tell you whether it still runs, and what to do when it does not.

## Quick reference

### Cron

```bash
crontab -l
crontab -e
crontab -u deploy -l
systemctl status cron
grep CRON /var/log/syslog
```

### Timers

```bash
systemctl list-timers --all
systemctl start backup.timer
systemctl enable --now backup.timer
systemctl cat backup.timer
systemd-analyze calendar '*-*-* 03:00'
```

### Logs

```bash
journalctl -u backup -n 50
journalctl -u backup --since today
journalctl -u backup -o cat
journalctl --disk-usage
journalctl --vacuum-time=14d
```

### Locking

```bash
flock -n /run/lock/backup.lock cmd
flock -w 30 /run/lock/x.lock cmd
exec 9>/run/lock/backup.lock
flock -n 9
lsof /run/lock/backup.lock
```

## Explained

### Cron

`crontab -l` lists your crontab, and `crontab -u deploy -l` reads another user's crontab with the right privileges. `systemctl status cron` says whether the daemon is alive; on RHEL the unit is crond and the log is `/var/log/cron`. `grep CRON /var/log/syslog` shows the last starts and the mail failures.

### Timers

`systemctl list-timers --all` is the schedule you can actually read: next run, last run, and the unit. `systemctl cat backup.timer` shows the OnCalendar line, and `systemd-analyze calendar '*-*-* 03:00'` explains it. `systemctl enable --now backup.timer` starts the schedule and the service.

### Logs

`journalctl -u backup -n 50` reads the last fifty lines; `--since` today narrows the window; -o cat drops the metadata. `journalctl --disk-usage` says how much the journal owns, and `--vacuum-time=14d` gives the space back.

### Locking

flock -n `/run/lock/backup.lock` cmd takes the lock or fails at once. flock -w 30 waits half a minute. The two-line form, exec 9>`/run/lock/backup.lock` and flock -n 9, holds the lock for a whole script. lsof and fuser name the process that owns it.

> **The honest caveat:** cron has no seconds and no overlap protection; a five-minute line starts the next run whether the last one ended or not.

> **The lesson:** a schedule you cannot read is a schedule you cannot trust.

## In one line

> **Automate the check, not the hope.** Twenty commands, four blocks, one unattended night.

**Read the timer**

```bash
systemctl list-timers --all
```
