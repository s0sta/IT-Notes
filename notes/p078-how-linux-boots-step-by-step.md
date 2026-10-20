---
id: p78
title: "How Linux boots, step by step"
slug: how-linux-boots-step-by-step
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, systemd, ITInfrastructure, Troubleshooting]
source: "LinkedIn post P78 · Linux series"
linkedin_date: 2027-03-28
design: pipeline
---

# How Linux boots, step by step

A server that will not boot is stuck at one specific stage. Knowing the six stages tells you where to look.

## Quick reference

1. **Firmware: UEFI or BIOS** — Checks the hardware and finds a disk it can boot from. · *POST*
2. **Bootloader: GRUB** — Shows the menu and loads the chosen kernel into memory. · `grub.cfg`
3. **Kernel** — Starts the CPU, memory and drivers. Hardware is detected. · *vmlinuz*
4. **initramfs** — A small temporary root with the drivers to mount the real one. · `initrd.img`
5. **systemd, PID 1** — The first process. It starts everything else. · *PID 1*
6. **Targets and services** — Disks, network, SSH and your apps. Then the login. · `multi-user.target`

## Explained

1. **Firmware: UEFI or BIOS.** The machine checks its hardware and looks for a disk it can boot from. Problems here look like no disk found, or a boot order that points at the wrong device.

2. **Bootloader: GRUB.** It shows the boot menu and loads the selected kernel and initramfs into memory. A broken GRUB config drops you to a grub> prompt. This is also where you can pick an older kernel if a new one fails.

3. **Kernel.** The kernel starts the CPUs, sets up memory and detects hardware. A kernel panic here is often a driver or hardware problem.

4. **initramfs.** A small temporary root filesystem with just enough drivers and tools to find and mount the real root filesystem, for example on LVM, RAID or an encrypted disk. If you land in an initramfs or emergency shell, the real root could not be mounted.

5. **systemd, PID 1.** The first real process. Everything else on the system is started by it, which is why it always has process ID 1.

6. **Targets and services.** systemd mounts the filesystems in `/etc/fstab`, brings up the network, starts SSH and your applications, and finally the login. A wrong line in fstab stops the boot right here.

Two commands worth knowing after any slow or strange boot: systemd-analyze blame shows which services took the longest, and `journalctl -b -1` shows the logs of the previous boot, the one that failed.

## In one line

> **Know the stage, find the problem.** A boot problem is stuck at one of these six steps.

**What slowed the last boot?**

```bash
systemd-analyze blame | head
```
