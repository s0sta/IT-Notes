---
id: p86
title: "Add a new disk to a Linux server"
slug: add-a-new-disk-to-a-linux-server
sections: [it]
topic: "Storage & infrastructure"
tags: [Linux, Storage, SysAdmin, ITInfrastructure, DevOps]
source: "LinkedIn post P86 · Linux series"
linkedin_date: 2027-04-15
design: pipeline
---

# Add a new disk to a Linux server

Adding a disk to a Linux server is a six-step job. Done in the right order, it is ten minutes. Done in the wrong order, it is a server that does not boot.

## Quick reference

1. **Find the disk** — The new disk has no partitions and no mount point. · `lsblk`
2. **Partition it** — One GPT partition across the whole disk. · `parted /dev/sdb`
3. **Make a filesystem** — Format the new partition. Double-check the name first. · `mkfs.ext4 /dev/sdb1`
4. **Mount it** — Create a folder and mount the partition there. · `mount /dev/sdb1 /data`
5. **Make it permanent** — Add it to `/etc/fstab` by UUID, with nofail. · `blkid /dev/sdb1`
6. **Test before reboot** — Mount everything from fstab and confirm it worked. · `mount -a && df -h`

## Explained

1. **Find the disk.** lsblk lists every block device. The new disk is the one with the right size, no partitions and no mount point, for example `/dev/sdb`. Never guess this from the name alone.

2. **Partition it.** `parted /dev/sdb`, then mklabel gpt and mkpart primary ext4 0% 100% creates one partition across the whole disk: `/dev/sdb1`. GPT handles disks larger than 2 TB, which old MBR tables cannot.

3. **Make a filesystem.** `mkfs.ext4 /dev/sdb1` formats the partition. Check the device name one more time before you press Enter. This step erases whatever is on it. XFS with mkfs.xfs is a common alternative for large data disks.

4. **Mount it.** `mkdir /data`, then `mount /dev/sdb1 /data`. The disk is usable now, but only until the next reboot.

5. **Make it permanent.** `blkid /dev/sdb1` shows the UUID. Add a line to `/etc/fstab`: `UUID=<uuid> /data ext4 defaults,nofail 0 2`. The UUID never changes, unlike the device name, and nofail means the server still boots if this disk is ever missing.

6. **Test before reboot.** `umount /data`, then `mount -a` mounts everything from fstab the same way the next boot will. `df -h` confirms `/data` is there with the right size. `findmnt --verify` checks fstab for mistakes.

That last step is the one people skip, and the one that saves you from an emergency console session.

## In one line

> **Test fstab before you reboot.** A bad fstab line is found now, or at 2 AM on a console.

**The fstab line**

```bash
UUID=<uuid>  /data  ext4  defaults,nofail  0 2
```
