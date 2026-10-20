---
id: p94
title: "6 port numbers every IT person should know"
slug: 6-port-numbers-every-it-person-should-know
sections: [it]
topic: "Networking & DNS"
tags: [Networking, CyberSecurity, ITSupport, SysAdmin, CCNA]
source: "LinkedIn post P94 · Linux + IT series"
linkedin_date: 2027-05-04
design: numbers
---

# 6 port numbers every IT person should know

Six port numbers that come up in almost every IT job. Knowing them turns a firewall rule or a scan result into something you can read at a glance.

## Quick reference

| Number | What | Why it matters | |
|:--|:--|:--|:--|
| **22** | SSH | Remote shell for Linux. Never open it to the world without keys. | TCP |
| **53** | DNS | UDP for normal lookups, TCP for big answers and transfers. | UDP/TCP |
| **443** | HTTPS | Encrypted web traffic. Almost everything runs over it now. | TCP |
| **3389** | RDP | Windows Remote Desktop. A favourite target for ransomware. | TCP |
| **3306** | MySQL / MariaDB | Database port. Keep it on localhost or a private network. | TCP |
| **587** | SMTP submission | Where mail clients send email, with login and TLS. | TCP |

## Explained

- **22** — SSH. The remote shell for Linux and network devices. It is scanned constantly, so it should only accept key-based logins, and ideally only from known IPs or a VPN.

- **53** — DNS. Normal lookups use UDP. Large responses and zone transfers between DNS servers use TCP on the same port. A firewall that only allows UDP 53 can cause strange, intermittent DNS failures.

- **443** — HTTPS. Encrypted web traffic. Today it carries websites, APIs, VPNs and much more. If only one inbound port is open on a web server, this is usually it, plus port 80 to redirect to it.

- **3389** — RDP. Windows Remote Desktop. Open to the internet, it is one of the most common ways ransomware groups get in. Put it behind a VPN or an RD Gateway with MFA.

- **3306** — MySQL and MariaDB. A database should almost never be reachable from the internet. Bind it to 127.0.0.1 or a private network, and allow only the application servers.

- **587** — SMTP submission. This is where mail clients and applications send email, with authentication and STARTTLS. Port 25 is for server-to-server delivery, and many cloud providers block it outbound.

A good habit: run `ss -tlnp` on Linux or `netstat -ano` on Windows and explain every listening port. Anything you cannot explain should not be open.

## In one line

> **Know the port, know the risk.** Every open port is a door. Count yours.

**What is open here?**

```bash
sudo ss -tlnp
```
