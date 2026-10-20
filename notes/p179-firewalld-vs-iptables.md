---
id: p179
title: "firewalld vs iptables"
slug: firewalld-vs-iptables
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Linux, RHEL, Firewall, RHCSA, Networking]
source: "LinkedIn post P179 · Cloud / DevSecOps series"
linkedin_date: 2027-11-18
design: compare
---

# firewalld vs iptables

On RHEL you will meet both firewalld and iptables, and knowing how they relate removes a lot of confusion. They are not really competitors: firewalld is a friendlier front end, and nftables does the work underneath both today.

## Quick reference

| | **FIREWALLD** | **IPTABLES** |
|:--|:--|:--|
| Model | Zones + services | Ordered rule chains |
| Live changes | Yes, then `--permanent` | Yes, but not saved by default |
| Persistence | Built in | Needs a save step |
| Backend | nftables today | nftables or legacy |
| RHEL default | Yes | Underneath |
| Best for | Servers, RHCSA | Fine-grained custom rules |

**FIREWALLD** (The modern front end): Zones and services, changes you can make live and then persist.

```bash
firewall-cmd --add-service=https
```

**IPTABLES** (The classic rule engine): Raw, ordered rules. Powerful, but you manage every detail.

```bash
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

- firewalld → the default on RHEL, and what RHCSA tests.
- iptables → know it, but let firewalld manage the rules.

## Explained

firewalld organises the firewall around zones and services. A zone is a trust level for an interface (public, internal, trusted), and a service is a named bundle of ports, like https or ssh. `firewall-cmd --add-service=https` opens a service in the live config, and adding `--permanent` saves it across reboots. This is the model RHCSA tests, and it is comfortable for day-to-day server work.

iptables is the classic tool: ordered chains of rules that each packet is checked against, top to bottom, until one matches. `iptables -A INPUT -p tcp --dport 443 -j ACCEPT` appends a rule. It is extremely precise, but you manage order, state and persistence yourself, and by default rules are lost on reboot unless you save them.

### How they relate

On modern RHEL, firewalld is the default and runs on top of nftables. Writing raw iptables rules at the same time as firewalld can cause confusing conflicts, because they are both trying to manage the same engine.

### The practical advice

Let firewalld manage the firewall on RHEL. Learn iptables so you can read older systems and understand what is happening underneath, but do not mix the two on the same box.

For RHCSA, know firewall-cmd cold: zones, services, ports, `--permanent` and `--reload`.

firewalld manages. iptables is underneath.
