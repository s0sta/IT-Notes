---
id: p175
title: "9 LVM commands every RHCSA needs"
slug: 9-lvm-commands-every-rhcsa-needs
sections: [it, devsecops]
topic: "Storage & infrastructure"
tags: [Linux, RHCSA, LVM, RHEL, SysAdmin]
source: "LinkedIn post P175 · Cloud / DevSecOps series"
linkedin_date: 2027-11-09
design: steps
---

# 9 LVM commands every RHCSA needs

LVM is the reason you can add space to a running Linux server without downtime, and it is a guaranteed part of the RHCSA. Nine commands take you from a raw disk to a volume you can grow on demand.

## Quick reference

### Build the stack — Disk to volume group

```bash
# Mark a disk as an LVM physical volume.
pvcreate /dev/sdb
# Create a volume group from one or more PVs.
vgcreate vg_data /dev/sdb
# Carve a logical volume out of the group.
lvcreate -L 10G -n lv_app vg_data
```

### Grow it live — The reason to use LVM

```bash
# Add another disk to the group for more space.
vgextend vg_data /dev/sdc
# Grow the LV and the filesystem in one step (-r).
lvextend -r -L +5G /dev/vg_data/lv_app
# Confirm the new size. No unmount, no reboot.
df -h /app
```

### Inspect — See what you have

```bash
# Physical volumes and their free space.
pvs
# Volume groups and how much is left.
vgs
# Logical volumes and their sizes.
lvs
```

## Explained

### Build the stack

`pvcreate /dev/sdb` marks a whole disk or partition as an LVM physical volume, the raw material.  
`vgcreate vg_data /dev/sdb` pools one or more physical volumes into a volume group, a single flexible space.  
`lvcreate -L 10G -n lv_app vg_data` carves a logical volume out of that group. You format and mount this, not the disk directly.

The layers are simple: physical volumes feed a volume group, and logical volumes are cut from the group.

### Grow it live

`vgextend vg_data /dev/sdc` adds another disk to the group when it runs low.  
`lvextend -r -L +5G /dev/vg_data/lv_app` is the command that matters. It grows the logical volume and, thanks to -r, resizes the filesystem on top in the same step. No unmount, no reboot, no downtime for users.  
`df -h` confirms the new size immediately.

### Inspect

`pvs`, `vgs` and `lvs` give a quick summary of physical volumes, groups and logical volumes, with free space at each level. Run them before and after any change.

The exam tip and the real-world tip are the same: practise `lvextend -r` until it is muscle memory. Running out of space on a production server at 2 a.m. is exactly when you want this to be automatic.

## In one line

> **Grow storage without downtime.** That one ability is why LVM is on every RHEL server.

**The one-liner**

```bash
lvextend -r -L +5G /dev/vg/lv
```
