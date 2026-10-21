---
id: p581
title: "Quiz: 3 host incident questions"
slug: quiz-3-host-incident-questions
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SRE, SysAdmin, DevOps, Troubleshooting]
source: "LinkedIn post P581 · PythonFixes series"
linkedin_date: 2030-06-13
design: quiz
---

# Quiz: 3 host incident questions

Phase one closes with three questions, and each one comes from a tool earlier in the phase. Answer before the reveal.

## Quick reference

**Q1. `df -h` shows 40% free but every write fails. What ran out?**

- a) The inode table on that filesystem
- b) The page cache
- c) The block device queue

> **Answer:** a) The inode table on that filesystem. `df -h` counts bytes, not inodes. `df -i` shows IUse% at 100%: blocks are free and there is no inode for a new file, so open() returns ENOSPC.

**Q2. What does the kernel's oom_score decide?**

- a) Which process the OOM killer picks
- b) How much swap a process may use
- c) The priority of the page cache

> **Answer:** a) Which process the OOM killer picks. The score runs 0 to 1000, driven by memory use and shifted by oom_score_adj. The highest score dies first, and -1000 protects a process from the killer.

**Q3. Why does a zombie's parent matter more than the zombie?**

- a) Only the parent can reap it
- b) The parent owns its memory
- c) The parent holds its file locks

> **Answer:** a) Only the parent can reap it. A zombie is already dead and holds no memory. It keeps a pid until its parent calls wait(); if the parent never does, the entry stays. Restart the parent.

## Explained

### Question one

`df -h` is clean at 40% and every write on that filesystem fails with ENOSPC. Nothing was deleted, no quota is set, and the application has been running for weeks. The bytes are free, so the question is what a file needs besides bytes, and why deleting one large log would not help. `df -i` is the command that answers it.

### Question two

The kernel picks a victim and kills it. Two processes hold the same resident memory, one has oom_score_adj at -900 and the other at 0, and the one at 0 dies. What does the score measure, and what does the adjustment do to it? Neither is a priority, a swap quota or a nice value.

### Question three

A child exits and its parent never calls wait(). The zombie holds a pid, a process table slot and nothing else. Why does the parent matter more than the dead child, and what happens to the zombie if the parent is restarted or exits first?

> **The honest caveat:** the answers are the easy part. At 03:00 you have one command, not three, so the habit is to know which one before the page arrives.

> **The lesson:** the tool names the cause, and the cause names the fix.

## In one line

> **Three answers, one pager.** The tool names the cause; the cause names the fix.

**Check your answer**

```bash
df -i; dmesg -T | tail
```
