---
id: p671
title: "Quiz: 3 automation questions"
slug: quiz-3-automation-questions-2
sections: [it, devsecops]
topic: "Linux"
tags: [Bash, Linux, DevOps, Automation, DevSecOps]
source: "LinkedIn post P671 · ShellSec series"
linkedin_date: 2031-01-09
design: quiz
---

# Quiz: 3 automation questions

Three questions close the series, and each one is a decision about work you cannot see. Answer before the reveal.

## Quick reference

**Q1. Why take a lock before the work starts, not after it finishes?**

- a) So the second run exits instead of colliding
- b) To make the script run faster
- c) To keep the log file small

> **Answer:** a) So the second run exits instead of colliding. Cron starts the next run on schedule, not when the last one ends. flock -n makes the second run exit 75 before it opens the data, so two writers never meet.

**Q2. Why is a silent cron failure worse than a crash?**

- a) A crash is noticed; silence looks normal
- b) A crash uses more CPU than silence
- c) Silent jobs simply run less often

> **Answer:** a) A crash is noticed; silence looks normal. A crash writes an exit code and usually a page. A silent failure leaves a target that looks like the last good backup, and the gap is found at restore time.

**Q3. Why verify the served certificate after a renew hook reloads?**

- a) The file changes; the process may not reload
- b) TLS caches the private key on disk
- c) Clients pin the certificate serial number

> **Answer:** a) The file changes; the process may not reload. nginx reads the certificate at start or reload. The file on disk proves the renewal, and only a fresh connection proves which certificate the process is serving.

## Explained

### Question one

The backup takes twelve minutes and the cron line starts it every five. What does flock -n change? The second run cannot start, so it exits 75 and leaves the data alone. Without the lock, both runs write the same files and both report success.

### Question two

Why is a silent cron failure worse than a crash? A crash leaves an exit code and usually a page. Silence leaves a target that looks like the last good backup, and the gap is found weeks later, when someone needs the restore. The wrapper's alert hook is the difference.

### Question three

Why must a renew hook verify the served certificate? Because the file changing is not the process reloading. nginx reads the certificate at start or reload, and only a fresh connection proves which one is live. The fingerprint comparison is the proof.

> **The honest caveat:** passing this quiz does not make the job safe; the wrapper, the timer and the alert do.

> **The lesson:** automation is only as good as the check after it.

That is the series. Fifty posts, five phases and twenty-five shell scripts, from the first host triage to this quiz. Thank you for following along.

## In one line

> **Automate it, then verify it.** Fifty posts, five phases, twenty-five scripts: the last three questions.

**Check the lock:** flock -n 9
