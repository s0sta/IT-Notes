---
id: p122
title: "9 checks before handing a laptop to a new employee"
slug: 9-checks-before-handing-a-laptop-to-a-new-employee
sections: [it]
topic: "IT operations & incidents"
tags: [ITSupport, Onboarding, EndpointSecurity, Windows, ITManagement]
source: "LinkedIn post P122 · Linux + IT series"
linkedin_date: 2027-07-08
design: checklist
---

# 9 checks before handing a laptop to a new employee

Onboarding is part of supporting 600 employees across 9 branches. The laptop a new hire receives on day one sets the standard for security and for how they see IT. Nine checks before handing it over.

## Quick reference

### Security

```powershell
# Disk encryption on
manage-bde -status
# Antivirus / EDR active
Get-MpComputerStatus
# No local admin for the user
net localgroup administrators
```

### Management

- **Joined to domain or Intune** — `dsregcmd /status`
- **Fully updated** — Windows, drivers, Office
- **Asset tag recorded** — serial, user, date

### Ready to work

- **MFA enrolled** — on day one, with the user
- **VPN and Wi-Fi tested** — from outside the office too
- **Files syncing** — OneDrive or the file share

## Explained

### Security

Disk encryption on. `manage-bde -status` should show BitLocker protection on. A lost laptop without encryption is a data breach. With encryption, it is just a lost laptop.  
Antivirus or EDR active. `Get-MpComputerStatus` for Defender, or your EDR console. Check it is running, up to date, and reporting to the central console.  
No local admin for the user. `net localgroup administrators`. Daily work as a standard user blocks a large share of malware. Admin rights, if really needed, should be separate and temporary.

### Management

Joined to the domain or Intune. `dsregcmd /status` shows whether the device is joined and managed. An unmanaged laptop gets no policies and no updates you control.  
Fully updated. Windows, drivers and Office, before it leaves IT. Otherwise the user's first morning is spent waiting for updates.  
Asset tag recorded. Serial number, user, date. When the person leaves, or the laptop is lost, you need to know exactly what to recover.

### Ready to work

MFA enrolled. Set it up with the user on day one, in person if possible. It is also the moment to explain how to report a suspicious email.  
VPN and Wi-Fi tested, including from outside the office if they will work remotely.  
Files syncing. OneDrive or the right file shares, so work is backed up from the first day.

## In one line

> **Day one sets the standard.** A secure laptop on day one is easier than fixing it later.

**A quick security look**

```powershell
manage-bde -status; dsregcmd /status
```
