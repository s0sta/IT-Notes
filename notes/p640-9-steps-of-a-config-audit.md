---
id: p640
title: "9 steps of a config audit"
slug: 9-steps-of-a-config-audit
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, Linux, DevSecOps, Audit, SRE]
source: "LinkedIn post P640 · ShellSec series"
linkedin_date: 2030-10-29
design: steps
---

# 9 steps of a config audit

A config audit is nine commands in three small groups: establish what is true, compare what changed, decide what to fix. Skip the first group and the other six are opinions.

## Quick reference

### Baseline — Write down what is true

```bash
# One file, one hash, one known-good value.
sha256sum /etc/ssh/sshd_config
# A copy you can diff, not a backup.
tar -C /etc -czf /var/lib/etc.tgz .
# Fingerprint every key you keep.
ssh-keygen -lf ~/.ssh/id_ed25519.pub
```

### Compare — Diff the tree, then the crypto

- **config_drift.sh -b /var/lib/etc-base** — Changed, added, removed; exit 1.
- **file_integrity.sh -c -b app.sha /srv** — The app tree, not just `/etc`.
- **tls_scan.sh -f hosts.txt --warn-days 21** — Protocols and the expiry window.

### Decide — Fix, then leave a check

- **cert_renew_check.sh -f certs.txt** — Renew what is inside 30 days.
- `ssh-keygen -R old.example.com` — Remove the host key you distrust.
- `systemctl reload sshd` — Reload the config, do not restart.

## Explained

### Baseline

The terminal starts with `sha256sum /etc/ssh/sshd_config`, one file and one known-good hash. Then `tar -C /etc -czf /var/lib/etc.tgz .` gives a copy you can diff, not a backup you hope restores. `ssh-keygen -lf ~/.ssh/id_ed25519.pub` gives every key a fingerprint you can compare later.

### Compare

`config_drift.sh -b /var/lib/etc-base` names changed, added and removed files and exits 1. `file_integrity.sh -c -b app.sha /srv` applies the same idea to the application tree. `tls_scan.sh -f hosts.txt --warn-days 21` checks the protocols and the expiry window together, because an old protocol and a short certificate are the same page.

### Decide

`cert_renew_check.sh -f certs.txt` names what is inside 30 days. `ssh-keygen -R old.example.com` removes a host key you no longer trust. `systemctl reload sshd` applies the config change without dropping the sessions you are trying to protect. Then write the owner and the date in the same ticket.

> **The honest caveat:** a baseline taken after the change freezes the wrong state. Write down the date and the change ticket before you run the first hash.

> **The lesson:** baseline, compare, decide, in that order, with an owner, a date and a check for every fix.

## In one line

> **Baseline, compare, then decide.** Nine commands, three groups, and a written owner for every fix.

**Start the clock**

```bash
sha256sum /etc/ssh/sshd_config
```
