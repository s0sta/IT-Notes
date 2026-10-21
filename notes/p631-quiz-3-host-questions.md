---
id: p631
title: "Quiz: 3 host questions"
slug: quiz-3-host-questions
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SRE, Troubleshooting, SysAdmin, Quiz]
source: "LinkedIn post P631 · ShellSec series"
linkedin_date: 2030-10-08
design: quiz
---

# Quiz: 3 host questions

Three host questions I ask in reviews, because the wrong answer sends you to the wrong tool under pressure.

## Quick reference

**Q1. Why can df and du disagree on a full host?**

- a) du counts sparse files twice
- b) Deleted files stay open
- c) df rounds to gigabytes

> **Answer:** b) Deleted files stay open. du walks names; a deleted file keeps its blocks until the last descriptor closes, and df counts blocks, not names.

**Q2. What does load average count that CPU usage misses?**

- a) Uninterruptible I/O wait
- b) Steal time only
- c) Idle threads

> **Answer:** a) Uninterruptible I/O wait. Load counts runnable and uninterruptible tasks, so a stalled disk raises load while the CPU sits idle.

**Q3. Why is the disk still full after deleting a log?**

- a) The inode is still open
- b) The filesystem is read-only
- c) df caches the old value

> **Answer:** a) The inode is still open. The process still holds the file descriptor. Truncate through `/proc/`\<pid>/fd or restart the writer.

## Explained

1. Why can df and du disagree on a full host?

> **Answer:** du walks names, and a deleted file keeps its blocks until the last descriptor closes. df counts blocks, so it sees the space as used while du cannot find a file that owns it. Check `lsof +L1` before you delete anything else.

2. What does load average count that CPU usage misses?

> **Answer:** runnable tasks plus tasks in uninterruptible sleep, usually waiting on disk. A stalled volume raises load while the CPU sits idle. Compare load with nproc and read `/proc/pressure/io` before you blame the processor.

3. Why is the disk still full after deleting a log?

> **Answer:** the process still holds the file descriptor. The name is gone and the blocks are not. Truncate through `/proc/`\<pid>/fd, or restart the writer, then confirm with df and `lsof +L1`.

### The pattern

Each answer replaces a number with a mechanism. That is the whole skill: df, du and load average all measure something narrower than their names suggest.

> **The honest caveat:** a deleted-but-open file explains a gap between df and du, not every gap; reserved blocks and snapshots explain the rest.

> **The lesson:** the number is not the cause.

## In one line

> **The number is not the cause.** df, du and load all measure less than their names suggest.

**Ask the host**

```bash
df -h; df -i; lsof +L1
```
