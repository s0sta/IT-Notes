---
id: p112
title: "How a ransomware attack unfolds, and where to stop it"
slug: how-a-ransomware-attack-unfolds-and-where-to-stop-it
sections: [it]
topic: "Security & hardening"
tags: [Ransomware, CyberSecurity, IncidentResponse, BlueTeam, ITSecurity]
source: "LinkedIn post P112 · Linux + IT series"
linkedin_date: 2027-06-15
design: pipeline
---

# How a ransomware attack unfolds, and where to stop it

I have handled a LockBit Black ransomware incident end to end: containment, a report to the NCA, a working decryptor from nomoreransom.org, and recovery. One lesson stays with me: the encryption is the last step, not the first. Most attacks follow the same six stages, and each one is a chance to stop it.

## Quick reference

1. **Initial access** — Phishing, exposed RDP, or an unpatched VPN. · *phish + RDP*
2. **Foothold** — Malware runs and connects back to the attacker. · *C2 beacon*
3. **Privilege escalation** — Stolen or cracked passwords lead to admin rights. · *admin creds*
4. **Lateral movement** — Spreads to servers, file shares and backups. · *RDP + SMB*
5. **Data theft** — Copies data out first, for double extortion. · *exfiltration*
6. **Encryption and ransom** — Files locked, backups targeted, a demand made. · *ransom note*

## Explained

1. **Initial access.** A phishing email, RDP open to the internet, or an unpatched VPN appliance. Stop it here with email filtering, MFA on every remote access, and fast patching of anything internet-facing.

2. **Foothold.** The malware runs and connects back to the attacker's server. EDR on endpoints and blocking unusual outbound traffic catch this stage.

3. **Privilege escalation.** The attacker collects passwords, often from memory or from a reused local admin password, until they reach admin rights. Separate admin accounts, LAPS and few Domain Admins slow this down.

4. **Lateral movement.** With admin rights, they move to servers, file shares and, very deliberately, the backup server. Network segmentation and restricting RDP and SMB between machines limit how far they get.

5. **Data theft.** Many groups copy data out before encrypting, so they can threaten to publish it. Large unusual uploads are a warning sign worth alerting on.

6. **Encryption and ransom.** Files are encrypted, online backups are deleted or encrypted, and the ransom note appears. Offline or immutable backups are what make this stage survivable.

If an incident does happen: isolate affected machines, preserve logs, report to the national authority, and check nomoreransom.org before anything else. Free decryptors exist for some families.

## In one line

> **Break the chain early.** Every stage you block makes the last one harder.

**The short list:** MFA + patched VPN/RDP + offline backups
