---
id: p178
title: "9 checks to harden a fresh RHEL server"
slug: 9-checks-to-harden-a-fresh-rhel-server
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Linux, RHEL, CyberSecurity, RHCSA, Hardening]
source: "LinkedIn post P178 · Cloud / DevSecOps series"
linkedin_date: 2027-11-16
design: checklist
---

# 9 checks to harden a fresh RHEL server

A fresh RHEL server is at its safest before it holds anything valuable, which is exactly when hardening is cheapest. Nine checks to run on day one, all within RHCSA scope.

## Quick reference

### Access

```bash
# SSH keys, not passwords
PasswordAuthentication no
# A sudo user, root login off
PermitRootLogin no
# Firewall on, least open
firewall-cmd --list-all
```

### The system

```bash
# SELinux enforcing
getenforce
# Patched and registered
dnf update; subscription-manager status
# Auto security updates
dnf-automatic
```

### Visibility

- **Time in sync** — `timedatectl`
- **Auditd running** — `systemctl is-active auditd`
- **Logs shipped off-box** — to a central server

## Explained

### Access

SSH keys, not passwords. Set `PasswordAuthentication no` in sshd_config once key login works, and automated password guessing becomes pointless.  
A sudo user, root login off. Create an admin user with sudo, then `PermitRootLogin no`. Every action now has a name behind it.  
Firewall on, least open. firewalld is on by default on RHEL. Check `firewall-cmd --list-all` and open only the services you actually serve.

### The system

SELinux enforcing. `getenforce` should say Enforcing. It is a real layer of defence, and turning it off to make something work is a habit worth breaking.  
Patched and registered. Register with subscription-manager for updates, then dnf update. An unpatched box is the easiest target there is.  
Automatic security updates. `dnf-automatic` applies security patches without waiting for someone to remember.

### Visibility

Time in sync. `timedatectl` should show the clock synchronized. Wrong time breaks TLS, Kerberos and every log timeline.  
Auditd running. The audit daemon records security-relevant events, including the SELinux denials you will need later.  
Logs shipped off-box. Send logs to a central server so an attacker cannot simply erase the local evidence.

None of this is advanced. It is the baseline that separates a server you can trust from one you merely hope about.

## In one line

> **Harden it before it has data.** Day one on a clean box beats cleanup after a breach.

**A 10-second look**

```bash
getenforce; firewall-cmd --list-all; sshd -T | grep -i root
```
