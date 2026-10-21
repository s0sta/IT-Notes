---
id: p669
title: "Four automation failures"
slug: four-automation-failures
sections: [it, devsecops]
topic: "IT operations & incidents"
tags: [Bash, Automation, DevOps, SRE, Linux]
source: "LinkedIn post P669 · ShellSec series"
linkedin_date: 2031-01-05
design: explainer
---

# Four automation failures

Four automation failures look like success from the outside. Each one is a missing check, not a missing tool.

## Quick reference

### Overlap

- Two runs share the same output directory
- The second reads a half-written file
- Cron starts both on schedule
- Fix: flock -n before the work

### Silent failure

- Cron mails output to a mailbox nobody reads
- Exit 0 hides the failed copy
- No metric, no alert, no page
- Fix: exit code plus an alert hook

### Stale process

- Certificate renewed on disk at 02:00
- The process still serves the old one
- Clients see the expiry date
- Fix: reload, then verify the served cert

### No retention

- Disk fills at 3% a week
- Deletion was a manual habit
- Nobody owns the cleanup
- Fix: a dry-run plan on a timer

> **Note:** Four failures that all look like success from the outside.

## Explained

### Overlap

Two runs share one output directory because the schedule is shorter than the work. The second reads a half-written file, both exit 0, and the record is wrong in a way neither reports. A lock is the fix: the second run exits 75 instead of colliding.

### Silent failure

Cron mails stdout to a mailbox nobody reads. The copy fails, the script exits 0 because the failure sat on the last line of a loop, and the next run looks like the last good one. An exit code and an alert hook are the fix. Silence is not success.

### Stale process

The certificate is renewed on disk at 02:00. The process read the old file at boot and keeps it in memory, so clients see the old date for weeks. Reload, then fetch the served certificate and compare it with the new one.

### No retention

The disk fills at 3% a week. Deletion was a manual habit, the person who owned it left, and no job owns the cleanup. A dry-run plan on a timer, with a risk note per path, turns habit into policy.

They combine: overlap plus silence gives a corrupted backup that reports success; no retention gives it a deadline. The verify tier separates them.

> **The honest caveat:** a lock and an alert do not make the job correct; they make its failures visible.

> **The lesson:** every automation failure is a check that was never run.

## In one line

> **Four failures, one silent disk.** Each one looks like success from the outside.

**Add the verify tier:** `cron_wrapper.sh --alert page.sh`
