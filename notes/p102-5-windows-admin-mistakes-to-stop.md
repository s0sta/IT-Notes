---
id: p102
title: "5 Windows admin mistakes to stop"
slug: 5-windows-admin-mistakes-to-stop
sections: [it]
topic: "Windows & Active Directory"
tags: [WindowsServer, ActiveDirectory, CyberSecurity, SysAdmin, ITSecurity]
source: "LinkedIn post P102 · Linux + IT series"
linkedin_date: 2027-05-23
design: dontdo
---

# 5 Windows admin mistakes to stop

Five Windows admin habits that save a few minutes and cost a lot when an attacker finds them.

## Quick reference

**1.** ❌ **Domain Admin for daily work** — One phished login gives away the whole domain.  
✅ **a normal account + an admin account** — Daily work as a user. Admin rights only when needed.

**2. Don't**

```powershell
netsh advfirewall set allprofiles state off
```

Turns the firewall off for every profile at once.

**Do instead**

open one port, not the whole firewall

Add a rule for the single port the app needs.

**3.** ❌ **same local admin password on every PC** — One stolen password or hash opens them all.  
✅ **Windows LAPS** — A unique, rotating local admin password per machine.

**4.** ❌ **restore a DC from an old snapshot** — Can roll AD back and break replication.  
✅ **AD-aware system state restore** — Use a backup method that knows it is restoring AD.

**5.** ❌ **RDP open to the internet** — Port 3389 is scanned all day by ransomware groups.  
✅ **VPN or RD Gateway + MFA** — Never expose RDP directly. Put a gate in front.

## Explained

1. Using a Domain Admin account for daily work
   Email, browsing and documents as Domain Admin means one phishing click hands over the entire domain. Instead: a normal account for daily work, and a separate admin account used only for admin tasks, ideally from a dedicated admin workstation.

2. Turning the whole firewall off
   `netsh advfirewall set allprofiles state off` makes an app work by removing all protection at once. Instead: add one inbound rule for the exact port and program the application needs.

3. The same local admin password on every PC
   Attackers who get that password, or its hash, from one machine can move to every other machine with it. Instead: Windows LAPS gives each computer a unique local admin password that rotates automatically and is stored in AD or Entra ID.

4. Restoring a domain controller from an old snapshot
   Rolling back a DC with an unsupported snapshot can cause USN rollback and break replication. Modern hypervisors with VM-Generation ID protect against much of this, but the safe path is still an AD-aware system state backup and a documented restore process.

5. RDP open to the internet
   Port 3389 is scanned around the clock, and exposed RDP is one of the most common ransomware entry points. Instead: reach RDP only through a VPN or an RD Gateway, with MFA.

Every one of these has been the first step in a real breach.

## In one line

> **Convenience is the attack surface.** Every shortcut above has been used in a real breach.

**Who is domain admin today?**

```powershell
Get-ADGroupMember 'Domain Admins'
```
