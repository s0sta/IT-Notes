---
id: p124
title: "5 password and access mistakes"
slug: 5-password-and-access-mistakes
sections: [it, devsecops]
topic: "Security & hardening"
tags: [CyberSecurity, IAM, PasswordSecurity, MFA, ITSecurity]
source: "LinkedIn post P124 · Linux + IT series"
linkedin_date: 2027-07-13
design: dontdo
---

# 5 password and access mistakes

Most breaches do not start with clever code. They start with a login. Five access habits that make it easy for attackers, and what to do instead.

## Quick reference

**1.** ❌ **one shared admin account** — Nobody knows who did what. Leavers keep access.  
✅ **named accounts + MFA** — Every action has a name. Remove one person, not a password.

**2.** ❌ **passwords.xlsx on the file share** — One compromised PC exposes every system.  
✅ **a password manager with sharing** — Encrypted, logged, and access can be removed.

**3.** ❌ **SMS codes for admin accounts** — SIM swaps and fake login pages can steal them.  
✅ **authenticator app or passkey** — Phishing-resistant MFA for anyone with admin rights.

**4.** ❌ **service account, password never expires** — Set once, known by many, never changed.  
✅ **gMSA or a secrets vault** — Passwords rotate automatically. No human knows them.

**5.** ❌ **admin / admin on a new device** — Default logins are the first thing bots try.  
✅ **change defaults on day one** — Before the device ever touches the network.

## Explained

1. One shared admin account
   When five people use the same admin login, the logs cannot tell you who did what, and someone who leaves the company still knows the password. Instead: named accounts for every person, with MFA. Removing access means disabling one account.

2. passwords.xlsx on the file share
   A spreadsheet of passwords is the first thing an attacker searches for after getting into one PC. Instead: a password manager with shared vaults for teams. It is encrypted, every access is logged, and you can remove someone's access in one click.

3. SMS codes for admin accounts
   SMS is better than nothing, but SIM swap attacks and fake login pages that relay the code in real time can defeat it. Instead: an authenticator app with number matching, or a passkey or hardware key for anyone with admin rights.

4. Service accounts whose passwords never expire
   They are created once, the password is shared with whoever set up the integration, and it never changes. Instead: group managed service accounts in Active Directory, or a secrets vault, so passwords rotate automatically and no person needs to know them.

5. Default logins on new devices
   Printers, cameras, switches and NAS boxes ship with admin and admin or similar. Bots try these within minutes of a device appearing online. Instead: change default credentials on day one, before the device is connected to the network.

## In one line

> **Identity is the new perimeter.** Protect logins like you protect servers.

**Start here:** MFA for every admin, this week
