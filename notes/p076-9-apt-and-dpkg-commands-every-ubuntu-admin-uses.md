---
id: p76
title: "9 apt and dpkg commands every Ubuntu admin uses"
slug: 9-apt-and-dpkg-commands-every-ubuntu-admin-uses
sections: [it]
topic: "Linux"
tags: [Linux, Ubuntu, Debian, SysAdmin, PatchManagement]
source: "LinkedIn post P76 · Linux series"
linkedin_date: 2027-03-23
design: terminal
---

# 9 apt and dpkg commands every Ubuntu admin uses

Most Ubuntu admins know apt install. These nine commands are what turn patching from a gamble into a routine.

## Quick reference

### Keep it current

```bash
# refresh the package lists. Installs nothing
sudo apt update
# exactly what would change
apt list --upgradable
# upgrade, after you have read the list
sudo apt upgrade
```

### What is installed, and why?

```bash
# installed vs available, and from which repository
apt-cache policy nginx
# ii means installed and healthy
dpkg -l | grep nginx
# which package owns this file?
dpkg -S /usr/sbin/nginx
```

### Stay in control

```bash
# freeze a version. Upgrades will skip it
sudo apt-mark hold nginx
# remove unused dependencies and old kernels
sudo apt autoremove --purge
# what changed, before you install it
apt changelog nginx | head -3
```

## Explained

### Keep it current

- `sudo apt update` — refreshes the list of available packages from the repositories. It installs nothing. Run it before anything else.
- `apt list --upgradable` — exactly which packages would change, and from which version to which. This is the list to read before you upgrade a production server.
- `sudo apt upgrade` — upgrades everything on that list. With the list already read, there are no surprises.

### What is installed, and why?

- `apt-cache policy nginx` — the installed version, the candidate version, and which repository each comes from. Essential when you have added third-party repos.
- `dpkg -l | grep nginx` — installed packages with their status. ii means installed and healthy. Anything else deserves a closer look.
- `dpkg -S /usr/sbin/nginx` — which package owns a file. Useful when you find a binary or config and need to know where it came from.

### Stay in control

- `sudo apt-mark hold nginx` — freezes a package at its current version. Upgrades skip it until you run apt-mark unhold. apt-mark showhold lists everything on hold.
- `sudo apt autoremove --purge` — removes dependencies nothing needs anymore, including old kernels that fill up `/boot`.
- `apt changelog nginx` — what changed in the new version, from the package maintainers. Security fix or a big behaviour change? Now you know before you install.

The habit worth keeping: update, read the list, then upgrade. Not `apt upgrade -y` in the dark.

## In one line

> **Read the list before you upgrade.** Thirty seconds of reading beats an hour of rollback.

**Try it**

```bash
sudo apt update && apt list --upgradable
```
