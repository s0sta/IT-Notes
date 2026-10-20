---
id: p304
title: "The security command cheat sheet"
slug: the-security-command-cheat-sheet
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Linux, CyberSecurity, CommandLine, SysAdmin, DevSecOps]
source: "LinkedIn post P304 · Visual series"
linkedin_date: 2028-09-05
design: cheatsheet
---

# The security command cheat sheet

At 03:00 the incident channel asks three things at once: what is listening, which key is on the box, and who logged in an hour ago. Twenty commands cover the answers.

## Quick reference

### TLS

```bash
openssl s_client -connect example.com:443
openssl x509 -in cert.pem -noout -dates
openssl verify -CAfile ca.pem cert.pem
openssl s_client -tls1_2 -connect host:443
openssl s_client -connect host:443 -brief
```

### Network

```bash
ss -tlnp
ss -tnp state established
nmap -sT -p- 10.0.0.5
nmap -sV --top-ports 100 10.0.0.5
tcpdump -i any -n port 443
```

### Keys

```bash
ssh-keygen -t ed25519 -C 'me@host'
ssh-keygen -lf id_ed25519.pub
ssh-keygen -y -f id_ed25519
ssh-keygen -p -f id_ed25519
ssh-copy-id -i id_ed25519.pub host
```

### Audit

```bash
lastb | head
who -a
last -a | head -20
journalctl -u sshd -n 50
grep -i 'failed' /var/log/auth.log
```

## Explained

### TLS

`openssl s_client -connect example.com:443` shows the chain the server actually sends. Add -brief when you only want the summary, or -tls1_2 to prove the old protocol still works. x509 -dates reads the expiry from a file, and verify -CAfile checks a chain against your own CA.

### Network

`ss -tlnp` lists listening sockets with the process that owns them. `ss -tnp state established` shows what is connected now. `nmap -sT -p-` scans every port, and -sV `--top-ports 100` fingerprints the common ones. tcpdump is the last word when the two hosts disagree.

### Keys

`ssh-keygen -t ed25519` creates the key. -lf prints the fingerprint you compare out of band, -y recovers the public key from the private one, and -p changes the passphrase. ssh-copy-id installs it on the host without hand-editing authorized_keys.

### Audit

lastb reads failed logins, `who -a` shows who is on the box now, and `last -a` is the history. `journalctl -u sshd` gives the daemon's own view, and grep on `auth.log` is the fast answer when the journal is gone.

> **The honest caveat:** lastb needs root and `/var/log/btmp`, and on RHEL the log is `/var/log/secure`, not `auth.log`.

> **The lesson:** four areas, five commands each, and most incident questions are answered before the first coffee.

## In one line

> **Type the command, read the answer.** Five per area beats fifty you cannot recall.

**Check a cert**

```bash
openssl x509 -in cert.pem -noout -dates
```
