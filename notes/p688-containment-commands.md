---
id: p688
title: "Containment commands"
slug: containment-commands
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, Linux, CommandLine, CyberSecurity, SRE]
source: "LinkedIn post P688 · IR series"
linkedin_date: 2031-02-18
design: cheatsheet
---

# Containment commands

The containment step is not a mood. It is a short list of commands, run in an order you can defend afterwards.

## Quick reference

### Host

```bash
ss -tlnp
ps aux --sort=-%cpu | head
ls -l /proc/$PID/fd | wc -l
systemctl isolate rescue.target
history -a; tail -20 ~/.bash_history
```

### Identity

```bash
passwd -l ana
chage -E 0 ana
pkill -KILL -u ana
loginctl terminate-user ana
crontab -r -u ana
```

### Edge

```bash
iptables -I INPUT -s 1.2.3.4 -j DROP
ufw deny from 1.2.3.4
nft list ruleset
conntrack -L | grep 1.2.3.4
dig +short api.example.com
```

### Flags

```bash
jq '.flags[]|select(.owner==null)'
jq -r '.flags[] | .key' flags.json
curl -s $FLAG_API/flags | jq .
curl -s $FLAG_API/flags | jq '.on'
jq '.flags[] | select(.on)' flags.json
```

## Explained

### Host

`ss -tlnp` shows what still answers. `ps aux --sort=-%cpu | head` finds the process that appeared at 03:04. `ls -l /proc/$PID/fd | wc -l` counts its open files. history -a; tail -20 ~/.bash_history shows what the last shell did. `systemctl isolate rescue.target` drops to a single-user shell.

### Identity

`passwd -l ana` locks the password, `chage -E 0 ana` expires the account, and `pkill -KILL -u ana` ends the processes that are already running. `loginctl terminate-user ana` closes the session, and `crontab -r -u ana` removes the persistence nobody looks at.

### Edge

`iptables -I INPUT -s 1.2.3.4 -j DROP` is still the fastest block on a host. `ufw deny from 1.2.3.4` is the same rule with a nicer face. conntrack -L | grep 1.2.3.4 shows the live connections, and `nft list ruleset` proves the rule is where you think it is.

### Flags

`jq '.flags[]|select(.owner==null)'` finds the flags nobody owns. `curl -s $FLAG_API/flags | jq .` reads the export without a dashboard. Pulling a flag is a change: record the key, the old value and the time.

> **The honest caveat:** these are host and file commands; the control plane, the cloud IAM and the SaaS admin need their own runbook.

> **The lesson:** a command is not containment; the order is.

## In one line

> **Contain the path, not the story.** Four families, one order: host, identity, edge, flags.

**Cut, then check**

```bash
ss -tlnp
```
