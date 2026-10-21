---
id: p670
title: "5 shell scripting mistakes"
slug: 5-shell-scripting-mistakes
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Linux, Scripting, DevOps, CyberSecurity]
source: "LinkedIn post P670 · ShellSec series"
linkedin_date: 2031-01-07
design: dontdo
---

# 5 shell scripting mistakes

A shell script is a promise that the next line runs. These five habits break it.

## Quick reference

**1.** ❌ **for f in $(ls \*.log)** — Word splitting breaks on spaces and ls output is not a list.  
✅ **for f in \*.log** — The shell expands the glob, sorted and safely quoted.

**2. Don't**

```bash
rm -rf $DIR/
```

An empty DIR becomes `rm -rf /` and spaces split the path.

**Do instead**

```bash
rm -rf -- "${DIR:?}/"
```

`${DIR:?}` aborts if unset or empty; quotes keep one argument.

**3. Don't**

No `set -e` in the script

A failed cd or curl is ignored, and the next line runs.

**Do instead**

```bash
set -euo pipefail at the top
```

An unhandled failure stops the script with a code.

**4.** ❌ **Cron job with no lock** — A slow run still holds the files when the next starts.  
✅ **flock -n 9 around the work** — The second run exits 75 instead of colliding.

**5.** ❌ **Failure sent to `/dev/null`** — A silent failure is found weeks later, in the bill.  
✅ **Alert on a non-zero exit** — The wrapper pages with the code it saw.

## Explained

### The five

1. Parsing ls: for f in $(ls \*.log) splits on spaces and trusts a listing that was never a list. Use for f in \*.log; the shell expands the glob and keeps each name whole.
   \2. Unquoted variables. `rm -rf $DIR/` turns an empty DIR into `rm -rf /`, and a space in the value into two arguments. Use `rm -rf -- "${DIR:?}/"`: the :? aborts when unset, and the quotes keep one argument.
   \3. No `set -e`. Without it, a failed cd or curl is ignored and the next line runs against the wrong directory. Start every script with `set -euo pipefail`.
   \4. No lock. A slow cron run still holds the files when the next one starts. flock -n 9 around the work makes the second run exit 75 instead of colliding.
   \5. Silent failure. Sending the error to `/dev/null` hides the one line that would explain the outage. Let the exit code leave the script, and give cron an alert hook.

### What they share

Each habit saves a line today and costs an incident later. None of them looks wrong in a code review, because the script does run.

> **The honest caveat:** `set -e` does not catch every failure; a command in a condition and a pipeline without pipefail both keep going.

> **The lesson:** the shell does exactly what you wrote, not what you meant.

## In one line

> **Quote it or lose it.** Five habits that turn a working script into a 03:00 page.

**Start with set -e**

```bash
set -euo pipefail
```
