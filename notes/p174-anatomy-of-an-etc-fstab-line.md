---
id: p174
title: "Anatomy of an /etc/fstab line"
slug: anatomy-of-an-etc-fstab-line
sections: [it, devsecops]
topic: "Storage & infrastructure"
tags: [Linux, RHCSA, Storage, SysAdmin, RHEL]
source: "LinkedIn post P174 · Cloud / DevSecOps series"
linkedin_date: 2027-11-07
design: anatomy
---

# Anatomy of an /etc/fstab line

`/etc/fstab` decides which disks get mounted at boot and how. RHCSA tests it, and one wrong line can stop a server from booting, so it is worth reading field by field. Each line has six, separated by spaces or tabs.

## Quick reference

```text
UUID=3f2a... /data ext4 defaults,nofail 0 2
```

| Part | Name | What it means |
|:--|:--|:--|
| `UUID=3f2a...` | What to mount | The device, by UUID. Stable, unlike `/dev/sdb1`. |
| `/data` | Where | The mount point. The folder it appears at. |
| `ext4` | Type | The filesystem: ext4, xfs, vfat, nfs. |
| `defaults,nofail` | Options | Mount flags. nofail lets the server boot if it is missing. |
| `0` | Dump | Backup flag for the old dump tool. Almost always 0. |
| `2` | fsck order | Boot-time check order. 1 for root, 2 for others, 0 to skip. |

## Explained

Field 1, what to mount. The device. Use UUID= from blkid, not `/dev/sdb1`, because device names can change when disks are added or reordered, while a UUID never does.

Field 2, where. The mount point: the existing folder where the filesystem appears, like `/data`. Create the folder first.

Field 3, type. The filesystem type: ext4, xfs (the RHEL default), vfat for EFI, or nfs for a network share. auto lets the system guess, but naming it is clearer.

Field 4, options. Mount flags, comma-separated. defaults covers the common set. The one worth knowing is nofail: with it, a missing or failed disk does not stop the boot, which is exactly what you want for a secondary data disk.

Field 5, dump. A flag for the ancient dump backup tool. On modern systems it is almost always 0.

Field 6, fsck order. The order filesystems are checked at boot. 1 for the root filesystem, 2 for other permanent disks, and 0 to skip the check, which you use for network or removable mounts.

> **The rule that saves you:** after editing fstab, never reboot blindly. Run `mount -a` to mount everything the way boot would, and `findmnt --verify` to catch mistakes. Fix them now, not from a rescue console.

## In one line

> **Test it before you reboot.** A bad fstab line drops the server to emergency mode.

**The safe check**

```bash
mount -a && findmnt --verify
```
