---
id: p103
title: "Quiz: 3 networking questions from IT interviews"
slug: quiz-3-networking-questions-from-it-interviews
sections: [it]
topic: "Networking & DNS"
tags: [Networking, CCNA, ITCareer, InterviewPrep, ITSupport]
source: "LinkedIn post P103 · Linux + IT series"
linkedin_date: 2027-05-25
design: quiz
---

# Quiz: 3 networking questions from IT interviews

Three networking questions that come up in IT interviews again and again. Try to answer before you read on.

## Quick reference

**Q1. How many usable host addresses does a /26 subnet have?**

- a) 64
- b) 62
- c) 30

> **Answer:** b) 62. A /26 has 64 addresses. One is the network address and one is broadcast, so 62 are usable.

**Q2. DNS normally uses UDP port 53. When does it use TCP 53 instead?**

- a) Never, DNS is UDP only
- b) For large answers and zone transfers
- c) Only for DNS over HTTPS

> **Answer:** b) For large answers and zone transfers. When a reply is too big for UDP, and for zone transfers between servers, DNS uses TCP on the same port.

**Q3. What does ARP do on a local network?**

- a) Finds the MAC address for an IP
- b) Gives out IP addresses
- c) Turns names into IP addresses

> **Answer:** a) Finds the MAC address for an IP. ARP asks who has 192.168.1.1 and gets the MAC address back. DHCP gives out IPs. DNS resolves names.

## Explained

1. How many usable host addresses does a /26 subnet have?

> **Answer:** \62. A /26 leaves 6 bits for hosts, which is 2 to the power of 6, so 64 addresses. The first is the network address and the last is the broadcast address, so 62 can be given to devices. A quick way to remember: /24 gives 254, and each extra bit halves it. /25 gives 126, /26 gives 62, /27 gives 30.

2. **DNS normally uses UDP port 53.** When does it use TCP 53?

> **Answer:** for large responses and zone transfers. When a reply does not fit in a UDP packet, the server marks it as truncated and the client asks again over TCP. Zone transfers between DNS servers always use TCP. This is why a firewall that only allows UDP 53 causes failures that are rare and hard to explain, especially with DNSSEC and big TXT records.

3. What does ARP do on a local network?

> **Answer:** it finds the MAC address for an IP address. Before a PC can send a frame to 192.168.1.1, it broadcasts "who has 192.168.1.1?" and the owner replies with its MAC address. The result is cached in the ARP table, which `ip neigh` shows on Linux and `arp -a` on Windows. Two devices answering for the same IP is how you spot an IP conflict, or ARP spoofing.

Interviews test the basics because real outages are so often caused by them.

## In one line

> **Interviews test the basics.** Because outages are usually caused by them.

**See your arp table**

```bash
ip neigh
```
