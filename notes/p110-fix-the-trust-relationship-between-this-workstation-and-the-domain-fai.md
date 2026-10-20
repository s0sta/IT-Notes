---
id: p110
title: "Fix: The trust relationship between this workstation and the domain failed"
slug: fix-the-trust-relationship-between-this-workstation-and-the-domain-fai
sections: [it]
topic: "Windows & Active Directory"
tags: [ActiveDirectory, Windows, ITSupport, Troubleshooting, SysAdmin]
source: "LinkedIn post P110 · Linux + IT series"
linkedin_date: 2027-06-10
design: steps
---

# Fix: The trust relationship between this workstation and the domain failed

"The trust relationship between this workstation and the primary domain failed." The user cannot log in, and the classic fix, leaving and rejoining the domain, is slow and resets the computer's group memberships. There is a faster way.

## Quick reference

### Diagnose — Is the secure channel broken?

```powershell
# False: the PC and the domain disagree on its password.
Test-ComputerSecureChannel
# The same check, with the error code and the DC used.
nltest /sc_verify:corp.local
# Check the clock. Kerberos fails beyond 5 minutes off.
w32tm /query /status
```

### Fix — Repair it without rejoining

```powershell
# Resets the machine password. Log in locally first.
Test-ComputerSecureChannel -Repair -Credential corp\admin
# Another way to reset the computer account password.
Reset-ComputerMachinePassword -Credential corp\admin
# Restart, then log in with a domain account.
Restart-Computer
```

### Prevent — Why it happened

- **Old snapshots of domain PCs** — A restored VM brings back an old machine password.
- **Duplicate computer names** — Two PCs with one name fight over one account.
- **Computer account reset in AD** — Check AD history before you blame the PC.

## Explained

Every domain computer has its own account in Active Directory with a password that the computer changes automatically. When the computer and AD disagree on that password, the secure channel breaks and domain logins fail.

### Diagnose

- `Test-ComputerSecureChannel` — returns False when the secure channel is broken. Run it from a local administrator account, or with cached credentials if they still work.
- `nltest /sc_verify:corp.local` — the same check with more detail: which domain controller was used and the exact error code.
- `w32tm /query /status` — check the time too. Kerberos fails when the clock is more than five minutes off, and that can look like a trust problem.

### Fix

- `Test-ComputerSecureChannel -Repair -Credential corp\admin` — resets the computer account password on both sides, using a domain account with rights to do it. No rejoin, no lost group memberships.
- `Reset-ComputerMachinePassword -Credential corp\admin` — another built-in way to do the same reset.
- `Restart-Computer` — then log in with a domain account again.

### Prevent

- **Old snapshots** — restoring a VM or a disk image of a domain PC brings back an old machine password. This is the most common cause.
- **Duplicate computer names** — two machines joined with the same name share one AD account and keep breaking each other.
- **Computer account reset in AD** — someone reset or deleted the account. Check before you blame the PC.

## In one line

> **Repair the channel. Skip the rejoin.** One PowerShell line, run as local admin, fixes most cases.

**The fix**

```powershell
Test-ComputerSecureChannel -Repair -Credential corp\admin
```
