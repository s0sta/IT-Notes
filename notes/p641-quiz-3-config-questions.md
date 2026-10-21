---
id: p641
title: "Quiz: 3 config questions"
slug: quiz-3-config-questions
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, Linux, DevSecOps, CyberSecurity, TLS]
source: "LinkedIn post P641 · ShellSec series"
linkedin_date: 2030-10-31
design: quiz
---

# Quiz: 3 config questions

Phase two closes with three questions about the checks that keep a config and crypto sweep honest. Answer each before the reveal.

## Quick reference

**Q1. Why must the baseline stay read-only while you audit?**

- a) So the tree cannot change under the check
- b) Because hashes are one-way
- c) So the baseline file stays small

> **Answer:** a) So the tree cannot change under the check. If the audit writes into the tree, it changes what it measures. A baseline you can edit is not evidence; keep it on another host and mount it read-only.

**Q2. Why does key type matter more than key length alone?**

- a) It fixes the algorithm and default hash
- b) Long keys are always weak
- c) It sets the file permissions

> **Answer:** a) It fixes the algorithm and default hash. The type sets the algorithm family and signature hash. An RSA key can still sign with SHA-1; ed25519 cannot. Length raises one cost, not the protocol.

**Q3. What does a certificate chain failure mean for the client?**

- a) It could not build a trusted path to a root
- b) The leaf private key is missing
- c) The server is offline

> **Answer:** a) It could not build a trusted path to a root. The client walks leaf to intermediate to a root in its trust store. A missing, expired or untrusted intermediate breaks that path even when the leaf is valid.

## Explained

### Question one

Your audit script writes a report into the tree it is checking. Why is that a problem? Because the next check hashes the report, the baseline no longer describes the system, and a file the script can edit is not evidence. Read-only is not a style choice; it is what makes the comparison meaningful.

### Question two

Two keys are both 4096 bits. One is ssh-rsa, one is ed25519. Why does the type matter more than the length? The type sets the algorithm family and signature hash. An RSA key can still sign with SHA-1; ed25519 cannot. Length raises the cost of one attack, not the protocol.

### Question three

A client reports a certificate chain failure. The leaf is valid and in date. What failed? The client could not build a trusted path from the leaf through an intermediate to a root in its trust store. A missing, expired or untrusted intermediate breaks that path before the leaf's dates are considered.

> **The honest caveat:** passing this quiz does not audit a host; the commands do.

> **The lesson:** a baseline must be read-only, a key type is a policy, and a chain is a path. A report is not a control.

## In one line

> **Three answers, one checklist.** A baseline, a key type and a chain: three things to check before the page.

**Check the chain**

```bash
openssl verify -CAfile ca.pem cert.pem
```
