---
id: p93
title: "9 Windows commands for network problems"
slug: 9-windows-commands-for-network-problems
sections: [it]
topic: "Windows & Active Directory"
tags: [Windows, Networking, ITSupport, Troubleshooting, SysAdmin]
source: "LinkedIn post P93 · Linux + IT series"
linkedin_date: 2027-05-02
design: steps
---

# 9 Windows commands for network problems

"The internet is down" is a symptom, not a diagnosis. Nine built-in Windows commands take you from the complaint to the exact cause.

## Quick reference

### This pc — What does the machine think?

```powershell
# IP, gateway, DNS servers and DHCP lease for each adapter.
ipconfig /all
# Clear the local DNS cache after a record changes.
ipconfig /flushdns
# The routing table. Check the default route is there.
route print
```

### The path — Where does it break?

```bash
# Reach an IP first. This rules DNS in or out.
ping -n 4 8.8.8.8
# Every hop on the way. Shows where packets stop.
tracert shop.example.com
# What DNS answers, and which server answered.
nslookup shop.example.com
```

### The service — Is the port really open?

```powershell
# Tests one TCP port. Look at TcpTestSucceeded.
Test-NetConnection shop.example.com -Port 443
# What uses a port, with the process ID.
netstat -ano | findstr :3389
# Repairs a broken network stack. Needs a restart.
netsh winsock reset
```

## Explained

### This PC

- `ipconfig /all` — the IP address, gateway, DNS servers and DHCP lease for every adapter. An address starting with 169.254 means the PC never got one from DHCP.
- `ipconfig /flushdns` — clears the local DNS cache. Use it after a DNS record changes and one PC still goes to the old address.
- `route print` — the routing table. No default route (0.0.0.0) means nothing outside the local network is reachable, and a VPN client can quietly change this.

### The path

- `ping -n 4 8.8.8.8` — test an IP address first. If this works but names do not, the problem is DNS, not the connection.
- `tracert shop.example.com` — every router on the way to the destination. Where the replies stop is where to look next.
- `nslookup shop.example.com` — what DNS answers, and which DNS server gave that answer. Compare it with `nslookup shop.example.com 1.1.1.1`.

### The service

- `Test-NetConnection shop.example.com -Port 443` — tests whether a specific TCP port is reachable. Many firewalls block ping, so this is the real test for a website, RDP or a database.
- `netstat -ano | findstr :3389` — what is listening on or connected to a port, with the process ID. Match the PID in Task Manager.
- `netsh winsock reset` — resets the Windows network stack when it is corrupted, often by old VPN or security software. It needs a restart.

> **The pattern:** name, path, port. Test all three and the cause is almost always clear.

## In one line

> **Ping is only the first question.** Name, path, port. Test all three before you call it fixed.

**The one that answers most**

```powershell
Test-NetConnection host -Port 443
```
