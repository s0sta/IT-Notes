---
id: p77
title: "9 checks before you patch a production server"
slug: 9-checks-before-you-patch-a-production-server
sections: [it]
topic: "Linux"
tags: [Linux, PatchManagement, SysAdmin, ITOperations, CyberSecurity]
source: "LinkedIn post P77 · Linux series"
linkedin_date: 2027-03-25
design: checklist
---

# 9 checks before you patch a production server

Patching is not optional. Patching blind is. Nine checks before you update a production Linux server.

## Quick reference

### Know what changes

```bash
# See what will update
apt list --upgradable
# Space in /var and /boot
df -h /var /boot
# Held packages known
apt-mark showhold
```

### Have a way back

- **Backup or snapshot done** — and a tested restore
- **Console access works** — provider console or iLO
- **Window agreed** — low traffic, people awake

### Confirm after

```bash
# Reboot needed?
ls /var/run/reboot-required
# Services came back
systemctl --failed
# The app answers
curl -sI http://localhost
```

## Explained

### Know what changes

- `apt list --upgradable` — read what will update. A kernel, a database or a web server deserves more attention than a small library.
- `df -h /var /boot` — packages are downloaded into `/var`, and kernels go to `/boot`. A full `/boot` halfway through a kernel update is a bad afternoon.
- `apt-mark showhold` — packages someone froze on purpose. Know why before you unhold anything.

### Have a way back

- **Backup or snapshot** — taken today, and from a system where you have tested a restore. A snapshot of a VM takes seconds.
- **Console access** — if the server does not come back after a reboot, SSH will not help. Make sure the provider console, iLO or iDRAC login works before you start.
- **Window agreed** — low traffic, and the people who know the application are awake and reachable.

### Confirm after

- `ls /var/run/reboot-required` — on Ubuntu, this file exists when an update needs a reboot. `/var/run/reboot-required.pkgs` lists which packages asked for it.
- `systemctl --failed` — every service came back after the update or reboot.
- `curl -sI http://localhost` — the application actually answers, not just the process. Use your real health check if you have one.

None of this is complicated. It is the difference between a patch that nobody notices and one everybody remembers.

## In one line

> **Patch with a plan, not with hope.** The patch takes five minutes. The plan makes it boring.

**The first command**

```bash
apt list --upgradable && df -h /boot
```
