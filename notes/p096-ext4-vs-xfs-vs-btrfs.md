---
id: p96
title: "ext4 vs XFS vs Btrfs"
slug: ext4-vs-xfs-vs-btrfs
sections: [it]
topic: "Storage & infrastructure"
tags: [Linux, Storage, SysAdmin, Filesystem, ITInfrastructure]
source: "LinkedIn post P96 · Linux + IT series"
linkedin_date: 2027-05-09
design: matrix
---

# ext4 vs XFS vs Btrfs

Three Linux filesystems you will meet on servers. Each one is the right answer somewhere.

## Quick reference

| | **ext4** | **XFS** | **Btrfs** |
|:--|:--|:--|:--|
| Maturity | ✅ Very mature | ✅ Very mature | 🟡 RAID 5/6 not advised |
| Default on | Debian, Ubuntu | RHEL, Rocky, Alma | Fedora, openSUSE |
| Shrink | ✅ Yes, offline | ❌ Not possible | ✅ Yes, online |
| Snapshots | ❌ Use LVM | ❌ Use LVM | ✅ Built in |
| Checksums | 🟡 Metadata only | 🟡 Metadata only | ✅ Data and metadata |
| Huge files, big disks | 🟡 Good | ✅ Excellent | 🟡 Good |

**How to pick**

- **ext4** → the safe default for most servers and VMs.
- **XFS** → large disks, big files, heavy parallel I/O.
- **Btrfs** → when you want snapshots and data checksums.

## Explained

ext4 is the long-time default on Debian and Ubuntu. Extremely mature, well understood, and every rescue tool supports it. It can grow online and shrink while unmounted. It checksums its metadata but not your data, and it has no snapshots of its own, so people pair it with LVM when they need them.

XFS is the default on RHEL, Rocky and Alma Linux. It shines with very large disks, very large files and many parallel writes, which is why it is common on file and database servers. Its one hard limit: an XFS filesystem cannot be shrunk. Plan your sizes, or be ready to copy the data to a new volume.

Btrfs is the default on Fedora and openSUSE. It has snapshots built in, checksums on data as well as metadata so silent corruption is detected, compression, and it can grow and shrink online. The honest caveat: its RAID 5 and 6 modes are still not recommended for important data. RAID 1 and 10 are fine.

### The practical choice

ext4 for most servers and VMs, especially if your team already knows it.  
XFS for big storage and heavy I/O, on the RHEL family where it is the default anyway.  
Btrfs when snapshots before upgrades and data checksums matter more than familiarity.

The most important feature of a filesystem is that someone on your team knows how to repair it at 3 AM.

`df -Th` shows what each of your filesystems uses.

## In one line

> **Boring is a feature here.** Pick the filesystem you know how to repair.

**Check what you run**

```bash
df -Th
```
