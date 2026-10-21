---
id: p658
title: "Security shell commands"
slug: security-shell-commands
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, Linux, CommandLine, CyberSecurity, SysAdmin]
source: "LinkedIn post P658 · ShellSec series"
linkedin_date: 2030-12-10
design: cheatsheet
---

# Security shell commands

Security work on a Linux host is mostly reading state that is already there. These are the commands I reach for, grouped by the question they answer. All of them are read-only and safe on a production host.

## Quick reference

### Users

```bash
last -F -i | head -20
sudo lastb -F -i | head -20
getent passwd | cut -d: -f1
awk -F: '$3==0{print $1}' /etc/passwd
passwd -S alice
id -nG alice
```

### Files

```bash
find / -xdev -perm -4000 -type f
find / -xdev -perm -2000 -type f
getfacl -R -p /srv
stat -c '%a %U:%G %n' /etc/shadow
ls -l /etc/cron.d/ /etc/cron.daily/
```

### Logs

```bash
journalctl -u sshd --since -24h
grep -Ei 'fail|invalid' /var/log/auth.log
ausearch -m USER_LOGIN -ts today
zgrep -i accepted /var/log/auth.log*
journalctl _COMM=sudo --since today
```

### Images

```bash
trivy image --severity HIGH,CRITICAL $IMG
trivy image --format json $IMG
docker scout cves nginx:1.27
crane digest nginx:1.27
cosign verify $IMAGE
```

## Explained

### Users

`last -F -i` shows sessions with a year, lastb shows failed attempts, getent passwd lists accounts, and the awk one-liner prints uid 0 accounts, which is the list that matters. `passwd -S alice` shows whether a password is locked, and `id -nG alice` lists the groups that decide what the account can touch.

### Files

`find -perm -4000` and -2000 list setuid and setgid binaries, `getfacl -R` shows the ACLs ls hides, and `stat -c` prints mode and owner in one line. The -xdev flag keeps the sweep on one filesystem.

### Logs

`journalctl -u sshd` answers "who tried", grep on `auth.log` answers "what failed", ausearch answers "what did the audit daemon see", and zgrep covers the rotated files. journalctl _COMM=sudo answers who used sudo.

### Images

trivy image scans a tag, crane digest resolves it to a digest, and cosign verify checks the signature before the gate trusts it. A digest is immutable; a tag is a label that can move.

> **The honest caveat:** every one of these reads what the local box can see, and a compromised host can lie to all of them.

> **The lesson:** know the command for the question, and the investigation is shorter.

## In one line

> **Know the state before you change it.** A short list per question beats fifty you cannot recall.

**A first look**

```bash
last -F -i; df -h; free -h
```
