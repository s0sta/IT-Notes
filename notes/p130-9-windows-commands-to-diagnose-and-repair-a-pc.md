---
id: p130
title: "9 Windows commands to diagnose and repair a PC"
slug: 9-windows-commands-to-diagnose-and-repair-a-pc
sections: [it]
topic: "Windows & Active Directory"
tags: [Windows, ITSupport, Troubleshooting, SysAdmin, PowerShell]
source: "LinkedIn post P130 · Linux + IT series"
linkedin_date: 2027-07-27
design: terminal
---

# 9 Windows commands to diagnose and repair a PC

A PC that is slow, crashing, or just acting strange does not always need a reinstall. These nine built-in Windows commands fix or diagnose most of it first. Run them in an elevated terminal.

## Quick reference

### Repair Windows itself

```powershell
# check and repair protected system files
sfc /scannow
# repair the image sfc relies on. Run sfc after
DISM /Online /Cleanup-Image /RestoreHealth
# scan the disk online. /f schedules a full fix
chkdsk C: /scan
```

### Reset the network

```powershell
# clear stale DNS entries
ipconfig /flushdns
# repair a broken network stack
netsh winsock reset
# confirm the machine can reach the internet
Test-NetConnection 8.8.8.8
```

### Check the hardware and logs

```powershell
# is the disk healthy?
Get-PhysicalDisk | ft FriendlyName, HealthStatus
# the last 20 system events
Get-WinEvent -LogName System -MaxEvents 20
# laptop battery health, in one file
powercfg /batteryreport
```

## Explained

### Repair Windows itself

`sfc /scannow` checks every protected system file against a known-good copy and repairs what is corrupt. The first thing to try for strange errors and crashes.  
`DISM /Online /Cleanup-Image /RestoreHealth` repairs the component store that sfc relies on. If sfc cannot fix something, run DISM, then run sfc again.  
`chkdsk C: /scan` scans the system disk online without a reboot. Add /f to schedule a full repair at the next restart if it finds problems.

### Reset the network

`ipconfig /flushdns` clears cached DNS entries, the fix when one PC keeps reaching the old address after a DNS change.  
`netsh winsock reset` repairs a corrupted network stack, often left behind by old VPN or security software. It needs a restart.  
`Test-NetConnection 8.8.8.8` confirms the machine can actually reach the internet, and the -Port form tests a specific service.

### Check the hardware and logs

`Get-PhysicalDisk | ft FriendlyName, HealthStatus` shows whether a disk reports itself as healthy. A failing disk explains a lot of slowness and freezing.  
`Get-WinEvent -LogName System -MaxEvents 20` shows the most recent system events. Repeated errors near a crash time point straight at the cause.  
`powercfg /batteryreport` writes a battery health report for a laptop, including how much capacity it has lost.

The order that saves a reinstall: DISM, then sfc, then check the disk and the event log.

## In one line

> **Repair before you reinstall.** Most strange Windows behaviour is a repairable file or a tired disk.

**Try it**

```powershell
DISM ... /RestoreHealth && sfc /scannow
```
