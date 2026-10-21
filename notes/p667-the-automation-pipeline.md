---
id: p667
title: "The automation pipeline"
slug: the-automation-pipeline
sections: [it, devsecops]
topic: "IT operations & incidents"
tags: [Bash, Automation, DevOps, SRE, Linux]
source: "LinkedIn post P667 · ShellSec series"
linkedin_date: 2030-12-31
design: architecture
---

# The automation pipeline

The backup runs every night. Nobody knows whether it started, whether it finished, or whether the file it wrote can be restored. The cron line is only the first of three tiers.

## Quick reference

- **Trigger:** Cron (CRON) · Systemd timer (TIMER) · Deploy hook (HOOK)
- **Run:** Wrapper (WRAP) · Lock file (LOCK) · Timeout (TIME) · Run log (LOG)
- **Verify:** Health check (CHECK) · Served cert (CERT) · Pager (PAGE)

**Request flow:** Cron → Wrapper → Lock file; Wrapper → Timeout; Wrapper → Run log; Wrapper → Health check → Pager; Systemd timer → Wrapper; Deploy hook → Wrapper; Served cert → Pager

**Around it:** Exit code (EXIT) · Runbook (RUN) · Cron mail (MAIL) · Pager (PAGE)

## Explained

### Trigger

The trigger tier starts the work. Cron is a clock; a systemd timer is a scheduler with a calendar; a deploy hook is an event. Each one can fire twice, so the work behind it must be idempotent. The trigger never owns data.

### Run

The run tier is one wrapper around one job. The wrapper takes the lock, sets the timeout, writes the log and passes the exit code on. The job does one thing and does not schedule itself. If the run cannot start because the lock is held, it exits 75 and says so.

### Verify

The verify tier decides whether the run counted. A health check reads the output, a certificate check compares the served cert with the new one, and the alert hook pages only after a failed check. This is the only tier allowed to wake a human.

The three tiers hand off through one exit code and one log line, which is what makes the path debuggable at 03:00. A trigger with no verify is a job that runs; a run with no lock is a job that overlaps itself.

> **The honest caveat:** a check that runs with the same credentials as the job can verify the wrong thing; keep the last check independent.

> **The lesson:** automation is a path with three tiers, and only the last one may page.

## In one line

> **Trigger, run, then verify.** Three tiers, and only the last one is allowed to page.

**Start at the trigger**

```bash
crontab -l
```
