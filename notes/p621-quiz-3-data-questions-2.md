---
id: p621
title: "Quiz: 3 data questions"
slug: quiz-3-data-questions-2
sections: [it, devsecops]
topic: "Backup & recovery"
tags: [Python, DataProtection, FinOps, DevOps, SRE]
source: "LinkedIn post P621 · PythonFixes series"
linkedin_date: 2030-09-15
design: quiz
---

# Quiz: 3 data questions

Three questions close the series, and each one is a decision you make about data you cannot see. Each answer is a test you can run this week.

## Quick reference

**Q1. Why is a backup without a restore test only a hope?**

- a) It proves a copy, not a restore
- b) The archive cannot be opened twice
- c) A checksum proves the bytes

> **Answer:** a) It proves a copy, not a restore. The job writes a file; only a restore proves the file can give the data back. A missing path or an unreadable archive stays invisible until the day you need it.

**Q2. What drives an S3 bill the most?**

- a) Stored bytes, class and requests
- b) The number of buckets
- c) The length of the bucket name

> **Answer:** a) Stored bytes, class and requests. Bytes times the class price, plus requests and retrieval. Cold data in STANDARD can cost six times its GLACIER price, and the line item never names the bucket.

**Q3. Why do orphaned volumes stay for years?**

- a) No owner sees the line item
- b) They cannot be deleted
- c) They are free while unattached

> **Answer:** a) No owner sees the line item. Billing is per account, not per team. An unattached disk has no owner to notice it, and the line item says EBS, not vol-0a1. A tag and a weekly report are the fix.

## Explained

### Question one

Why is a backup without a restore test only a hope? Because the job proves a copy exists, not that it works. A missing path or an unreadable archive stays invisible until the day you need it, and the first restore is the worst time to find out.

### Question two

What drives an S3 bill? Stored bytes times the class price, plus requests and retrieval. A large bucket of cold data in STANDARD can cost six times what it would in GLACIER, and the line item never names the bucket.

### Question three

Why do orphaned volumes stay for years? Because billing is per account, not per team. An unattached disk has no owner to notice it, and the line item says EBS, not vol-0a1. A tag and a weekly report are the fix.

> **The honest caveat:** passing this quiz does not make a backup restorable or a bill correct. The drill and the inventory do, and both are work you have to run.

> **The lesson:** data costs money until someone proves it is useful.

That is the series. Fifty posts, five phases and twenty-five Python tools, from the first host incident to this quiz. Thank you for following along.

## In one line

> **Back it up, then prove it.** Fifty posts end with the copy you can actually restore.

**Run the drill**

```bash
python3 restore_drill.py backup.tar
```
