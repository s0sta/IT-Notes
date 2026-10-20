---
id: p79
title: "5 Bash script mistakes that bite in production"
slug: 5-bash-script-mistakes-that-bite-in-production
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Linux, DevOps, Automation, ShellScripting]
source: "LinkedIn post P79 · Linux series"
linkedin_date: 2027-03-30
design: dontdo
---

# 5 Bash script mistakes that bite in production

Bash scripts run backups, deployments and cleanups on almost every server. Five mistakes that work fine in testing and fail in production.

## Quick reference

**1. Don't**

```bash
rm $file
```

A name with a space becomes two names. Or worse.

**Do instead**

```bash
rm -- "$file"
```

Quote every variable. -- stops names starting with -.

**2. Don't**

```bash
cd /opt/app; rm -rf build
```

If cd fails, rm runs in whatever folder you are in.

**Do instead**

```bash
cd /opt/app || exit 1
```

Stop the script the moment cd fails.

**3. Don't**

```bash
for f in $(ls *.log); do
```

Breaks on spaces and unusual file names.

**Do instead**

```bash
for f in *.log; do
```

Let the shell expand the glob. It handles every name.

**4. Don't**

```bash
tmp=/tmp/backup.tmp
```

A fixed name can collide with another run, or be abused.

**Do instead**

```bash
tmp=$(mktemp)
```

A unique temp file. Remove it with a trap on EXIT.

**5. Don't**

```bash
./deploy.sh
```

Never checked. Bugs show up in production first.

**Do instead**

```bash
shellcheck deploy.sh
```

Finds quoting bugs and traps before they run.

## Explained

1. `rm $file`
   Without quotes, a file name with a space becomes two arguments, and a name like -rf becomes an option. Instead: `rm -- "$file"`. Quote every variable, every time. The -- tells the command that options have ended.

2. `cd /opt/app; rm -rf build`
   If the folder does not exist or cannot be entered, cd fails and the next command runs in whatever directory the script is in. Instead: `cd /opt/app || exit 1`, or `set -e` at the top of the script.

3. for f in $(ls \*.log)
   Parsing ls output breaks on spaces, newlines and odd characters in file names. Instead: `for f in *.log; do`. The shell expands the glob itself and handles every name correctly.

4. `tmp=/tmp/backup.tmp`
   A fixed temp file name collides when two runs overlap, and on a shared system another user can create that file first. Instead: `tmp=$(mktemp)`, and trap '`rm -f "$tmp"'` EXIT so it is cleaned up even if the script fails.

5. `./deploy.sh, never checked`
   Most of the mistakes above are found automatically. Instead: `shellcheck deploy.sh`. It is free, fast, and explains every warning with a link.

And at the top of every script: `set -euo` pipefail. Stop on errors, stop on unset variables, and do not hide failures inside pipes.

## In one line

> **Scripts are code. Treat them like it.** Quote everything, check it, and fail early.

**Add to every script**

```bash
set -euo pipefail; trap 'rm -f "$tmp"' EXIT
```
