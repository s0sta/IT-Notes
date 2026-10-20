---
id: p100
title: "9 Active Directory hygiene checks"
slug: 9-active-directory-hygiene-checks
sections: [it]
topic: "Windows & Active Directory"
tags: [ActiveDirectory, WindowsServer, CyberSecurity, SysAdmin, ITSecurity]
source: "LinkedIn post P100 · Linux + IT series"
linkedin_date: 2027-05-18
design: checklist
---

# 9 Active Directory hygiene checks

Active Directory does not break all at once. It drifts: old accounts, extra admins, forgotten computers. Nine checks to run every quarter.

## Quick reference

### Accounts

- **Inactive users disabled** — `Search-ADAccount -AccountInactive`
- **No passwords that never expire** — check PasswordNeverExpires
- **Few Domain Admins** — `Get-ADGroupMember 'Domain Admins'`

### Machines

- **Stale computers removed** — inactive for 90+ days
- **LAPS on every PC** — unique local admin passwords
- **Replication healthy** — `repadmin /replsummary`

### The domain

- **DCs pass dcdiag** — `dcdiag /q`
- **AD backup tested** — system state + a test restore
- **krbtgt rotated** — on a schedule, twice each time

## Explained

### Accounts

- **Inactive users disabled** — `Search-ADAccount -AccountInactive -UsersOnly` finds accounts that have not logged in for a while. Former employees and old test accounts are a favourite entry point.
- **No passwords that never expire** — check for PasswordNeverExpires on user accounts. Service accounts are the usual culprits. Group managed service accounts (gMSA) solve this properly.
- **Few Domain Admins** — `Get-ADGroupMember 'Domain Admins'`. Every name on that list should be a person who needs it, using a separate admin account. Fewer is better.

### Machines

- **Stale computers removed** — computer accounts that have not been active for 90 days or more. Disable first, delete later.
- **LAPS on every PC** — Windows LAPS gives each machine a unique, rotating local admin password. Without it, one stolen local admin password often works on every PC.
- **Replication healthy** — `repadmin /replsummary` shows replication failures between domain controllers. Silent replication problems turn into strange login issues.

### The domain

- **DCs pass dcdiag** — `dcdiag /q` prints only the errors. A clean run is the goal.
- **AD backup tested** — a system state backup of at least one DC, and a test restore in an isolated lab. AD is the one system everything else depends on.
- **krbtgt rotated** — the password of the krbtgt account signs every Kerberos ticket. Rotate it on a schedule, twice each time with replication in between, using Microsoft's documented process.

## In one line

> **AD drifts. Check it on purpose.** Every stale account is a door nobody is watching.

**Find inactive users**

```powershell
Search-ADAccount -AccountInactive -UsersOnly
```
