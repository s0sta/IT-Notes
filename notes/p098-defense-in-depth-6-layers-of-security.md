---
id: p98
title: "Defense in depth: 6 layers of security"
slug: defense-in-depth-6-layers-of-security
sections: [it, devsecops]
topic: "Security & hardening"
tags: [CyberSecurity, InfoSec, BlueTeam, ITSecurity, DefenseInDepth]
source: "LinkedIn post P98 · Linux + IT series"
linkedin_date: 2027-05-13
design: stack
---

# Defense in depth: 6 layers of security

No security control is perfect. Defense in depth means stacking layers so that when one fails, the next one stops the attack. Six layers, from the data outward.

## Quick reference

*From the data outward*

1. **Data** — Encryption, least access, backups you can restore. · *encrypt + 3-2-1*
2. **Application** — Updates, strong logins, input checks, a WAF. · *MFA + WAF*
3. **Server** — Patching, hardening, only the services you need. · *patch + harden*
4. **Network** — Firewalls, segmentation, VPN or zero trust. · *VLAN + firewall*
5. **Endpoint** — EDR, disk encryption, no local admin rights. · *EDR + BitLocker*
6. **People** — Phishing awareness and an easy way to report. · *training*

## Explained

- **Layer 1** — Data. The thing attackers actually want. Encrypt it at rest and in transit, give access only to people who need it, and keep backups that are offline or immutable and have been restored at least once.

- **Layer 2** — Application. Keep it updated, require strong authentication with MFA, validate input, and put a web application firewall in front of anything public.

- **Layer 3** — Server. Patch on a schedule, remove services you do not use, harden SSH and RDP, and log to somewhere the attacker cannot easily erase.

- **Layer 4** — Network. Firewalls that deny by default, segmentation so a compromised printer cannot reach the finance server, and remote access through a VPN or a zero-trust gateway rather than open ports.

- **Layer 5** — Endpoint. EDR on laptops and servers, full disk encryption, and no local admin rights for daily work. Most attacks start on an endpoint.

- **Layer 6** — People. Phishing awareness, and just as important, an easy and blame-free way to report a suspicious email or a mistake within minutes.

Why layers matter: a phishing email gets past the filter. The user clicks. EDR blocks the payload. Even if it did not, segmentation limits the spread, and offline backups make the ransom note irrelevant.

If you can only start with three things: MFA everywhere, patching on a schedule, and backups you have tested.

## In one line

> **No single layer is enough.** Attackers need one gap. Make them find six.

**Start with these three:** MFA + patching + tested backups
