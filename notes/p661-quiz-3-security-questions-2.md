---
id: p661
title: "Quiz: 3 security questions"
slug: quiz-3-security-questions-2
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, CyberSecurity, DevSecOps, SecOps, Linux]
source: "LinkedIn post P661 · ShellSec series"
linkedin_date: 2030-12-17
design: quiz
---

# Quiz: 3 security questions

Phase four ends with three questions. Each one comes from a script in this phase, and each answer is a design decision, not a command.

## Quick reference

**Q1. Why does a setuid file need a baseline?**

- a) Because the bit is rare
- b) Because the change is what matters
- c) Because root owns the file

> **Answer:** b) Because the change is what matters. The bit is common; a new one is the finding. A list of approved files is the only definition of normal, so the sweep can tell an install from an intrusion.

**Q2. Why mask a secret in the scan output?**

- a) Because the value is long
- b) Because the report travels
- c) Because the file is binary

> **Answer:** b) Because the report travels. The report goes to a terminal, a CI log, a ticket and a screenshot. Printing the value copies the secret into each of them, so the scanner becomes the leak.

**Q3. Why does an allowlist need an owner?**

- a) Because CVEs expire
- b) Because an unowned exception never ends
- c) Because trivy needs a name

> **Answer:** b) Because an unowned exception never ends. An exception without an owner is permanent by default. An owner and an expiry make it a decision that gets reviewed, not a line nobody remembers adding.

## Explained

### Question one

Why does a setuid file need a baseline? Because the bit is not rare; the change is. A package upgrade adds one, an admin adds one to fix a permission error, and an intruder adds one for persistence. Without a list of what was approved yesterday, the sweep cannot tell today's file from last year's. The baseline is the definition of normal.

### Question two

Why mask a secret in the scan output? Because the output travels: to a terminal, a CI log, a ticket, a screenshot. A scan that prints the value copies the secret into every one of those places, and the report becomes the leak. Printing the key and four stars is enough to find the line and fix it.

### Question three

Why does an allowlist need an owner? Because an exception with no owner is permanent. A CVE that did not apply at build time may apply after the next dependency, and only a person who knows the context can decide. The owner and the expiry date are what make the exception a decision instead of a habit.

> **The honest caveat:** knowing the answers does not run the sweep; the cron line does.

> **The lesson:** a security check is a decision written down, and the writing is the hard part.

## In one line

> **Decide once, check forever.** Three answers, and one cron line that keeps them true.

**Run the sweep:** `suid_watch.sh /`
