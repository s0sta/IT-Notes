---
id: p591
title: "Quiz: 3 access questions"
slug: quiz-3-access-questions
sections: [it, devsecops]
topic: "Security & hardening"
tags: [CyberSecurity, Quiz, Identity, DevSecOps, TLS]
source: "LinkedIn post P591 · PythonFixes series"
linkedin_date: 2030-07-07
design: quiz
---

# Quiz: 3 access questions

Three questions come back in every access review, and each one is a join or a date rather than a scanner.

## Quick reference

**Q1. Why can a certificate be valid and still fail?**

- a) Its chain is incomplete or out of order
- b) Its key is shorter than 2048 bits
- c) The CA has no OCSP responder

> **Answer:** a) Its chain is incomplete or out of order. The leaf date is one check. A missing or misordered intermediate, or a key that does not match, fails the handshake while every date is still in range.

**Q2. What must a leaver audit join?**

- a) HR leavers to access exports
- b) Password hashes to expiry dates
- c) Certificates to private keys

> **Answer:** a) HR leavers to access exports. HR knows the last day and the systems know the account. Neither file is a finding on its own; the gap between them is the access that survived.

**Q3. Why is sudo drift a security event?**

- a) Privilege grows without a change request
- b) sudo becomes slower after edits
- c) It changes file ownership

> **Answer:** a) Privilege grows without a change request. A new NOPASSWD line or a wildcard turns a scoped grant into full root. The change usually arrives as a small favour and is never reviewed as a privilege change.

## Explained

### Question one

Why can a certificate be valid and still fail? The leaf date is one check. A missing or misordered intermediate, or a key that does not match, fails the handshake while every date is still in range. The browser error will name the host, not the tier. A bundle can be ordered wrong and still contain a valid leaf.

### Question two

What must a leaver audit join? HR knows the last day and the systems know the account. Neither file is a finding on its own; the gap between them is the access that survived. An active flag and a recent login are two different findings. A review that reads one file is a guess.

### Question three

Why is sudo drift a security event? A new NOPASSWD line or a wildcard turns a scoped grant into full root. The change usually arrives as a small favour and is never reviewed as a privilege change. The diff is the review that catches it.

> **The honest caveat:** a quiz cannot tell you which account is exposed. Run the audit on the real export, take the exit code, and read the lines it prints. A clean exit only means the files it read were clean.

> **The lesson:** the date, the join and the diff are the whole review.

## In one line

> **Valid is not the same as safe.** Three answers that decide whether the review can be trusted.

**Check the exit**

```bash
python3 cert_bundle_check.py; echo $?
```
