---
id: p590
title: "9 checks before an access review"
slug: 9-checks-before-an-access-review
sections: [it, devsecops]
topic: "Security & hardening"
tags: [AccessControl, CyberSecurity, Identity, DevSecOps, Compliance]
source: "LinkedIn post P590 · PythonFixes series"
linkedin_date: 2030-07-04
design: checklist
---

# 9 checks before an access review

An access review is a meeting with a spreadsheet, and the spreadsheet is usually the weakest part. Nine checks in three groups decide whether the meeting can produce a decision.

## Quick reference

### People

- **Leavers list is current** — HR export, dated
- **Movers are included** — promotion, transfer
- **Contractors are listed** — agency and temp

### Systems

- **Every system is named** — SSO, cloud, local
- **Service accounts owned** — one owner per account
- **Tokens and keys counted** — not just passwords

### Evidence

- **Last login is real** — system log, not HR
- **Reviewer signs off** — name and date
- **Fixes have tickets** — one per revocation

## Explained

### People

The leavers list is current: an HR export with a date, not a memory of who left. Movers are included, because a promotion changes what an account can reach. Contractors are listed too; an agency account with no end date is a leaver waiting to happen.

### Systems

Every system is named: SSO, cloud, local, and the admin console nobody put in the inventory. Service accounts have an owner, because an account with no owner has no one to disable it. Tokens and keys are counted alongside passwords; a token that outlives its owner is the same finding with a longer date.

### Evidence

Last login comes from the system, not from HR. The reviewer signs off with a name and a date, so the decision has an author. Every fix has a ticket, one per revocation, or the review becomes a document that nobody closes.

> **The honest caveat:** a review is a snapshot. Between two reviews, a leaver can keep a token that no export shows, which is why the offboarding audit runs on the event and not only here.

> **The lesson:** an access review is only as good as the join behind it.

## In one line

> **Access review starts with a join.** A review without the leaver join is a list of names.

**Run the join**

```bash
python3 offboarding_audit.py
```
