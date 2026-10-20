---
id: p119
title: "9 nmap commands to check your own network"
slug: 9-nmap-commands-to-check-your-own-network
sections: [it, devsecops]
topic: "Security & hardening"
tags: [CyberSecurity, Networking, BlueTeam, Nmap, InfoSec]
source: "LinkedIn post P119 · Linux + IT series"
linkedin_date: 2027-07-01
design: terminal
---

# 9 nmap commands to check your own network

Attackers scan your network whether you do or not. Scanning it yourself, regularly, means you see the forgotten open port first. One rule before anything else: only scan networks you own or have written permission to test.

## Quick reference

### What is on the network?

```bash
# host discovery only, no port scan
nmap -sn 192.168.10.0/24
# the 100 most common ports, fast
nmap --top-ports 100 192.168.10.20
# all 65535 ports. Finds the forgotten ones
nmap -p- 192.168.10.20
```

### What exactly is running?

```bash
# service versions: what needs patching
nmap -sV -p 22,443 192.168.10.20
# operating system guess. Needs root
sudo nmap -O 192.168.10.20
# UDP ports. SNMP open is worth a look
sudo nmap -sU -p 53,161 192.168.10.1
```

### Check and keep the results

```bash
# which TLS versions and ciphers are offered
nmap --script ssl-enum-ciphers -p 443 shop.example.com
# skip ping. Filtered = a firewall answers for it
nmap -Pn -p 3389 203.0.113.5
# save results. Compare next month: what changed?
nmap -sV 192.168.10.0/24 -oN scan-may.txt
```

## Explained

### What is on the network?

`nmap -sn 192.168.10.0/24` does host discovery only. Which IP addresses answer, without scanning ports. Unknown devices are the first thing to investigate.  
`nmap --top-ports 100 192.168.10.20` checks the 100 most common ports. Fast, and catches most services.  
`nmap -p- 192.168.10.20` checks all 65,535 TCP ports. Slower, but this is where forgotten admin panels and test services show up.

### What exactly is running?

`nmap -sV -p 22,443 192.168.10.20` does service and version detection. The output is your patch list: old OpenSSH, old nginx, old anything.  
`sudo nmap -O 192.168.10.20` guesses the operating system. Useful for finding devices nobody documented.  
`sudo nmap -sU -p 53,161 192.168.10.1` scans UDP ports, which a normal scan skips. SNMP with a default community string is a classic finding on printers and switches.

### Check and keep the results

`nmap --script ssl-enum-ciphers -p 443 shop.example.com` shows which TLS versions and ciphers a server offers. TLS 1.0 and 1.1 should be gone.  
`nmap -Pn -p 3389 203.0.113.5` skips the ping check, for hosts that block it. filtered means a firewall is dropping the traffic; open from the internet on 3389 is an urgent fix.  
`nmap -sV 192.168.10.0/24 -oN scan-may.txt` saves the results. Next month, compare. New open ports are changes someone should be able to explain.

## In one line

> **See what attackers see. First.** Scan your own network on a schedule, and compare the results.

**Try it**

```bash
nmap --top-ports 100 your-public-ip
```
