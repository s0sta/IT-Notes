---
id: p83
title: "5 disk mistakes that lose data"
slug: 5-disk-mistakes-that-lose-data
sections: [it]
topic: "Storage & infrastructure"
tags: [Linux, Storage, SysAdmin, DataProtection, DevOps]
source: "LinkedIn post P83 · Linux series"
linkedin_date: 2027-04-08
design: dontdo
---

# 5 disk mistakes that lose data

Disk commands do exactly what you type, instantly, with no undo. Five mistakes that lose data, and the check that prevents each one.

## Quick reference

**1. Don't**

```bash
dd if=ubuntu.iso of=/dev/sda
```

One wrong letter and you overwrite the system disk.

**Do instead**

```bash
lsblk -o NAME,SIZE,MODEL,MOUNTPOINT
```

Confirm the target first: size, model, mounted or not.

**2. Don't**

```bash
mkfs.ext4 /dev/sdb1
```

Formats instantly. The wrong partition means data gone.

**Do instead**

```bash
blkid /dev/sdb1
```

Already has a filesystem? Stop and look before you format.

**3. Don't**

```bash
/dev/sdb1  /data  ext4  defaults  0 2
```

Device names can change after a `reboot`.

**Do instead**

```bash
UUID=3f2a...  /data  ext4  defaults,nofail  0 2
```

UUIDs do not change. nofail keeps the boot going.

**4. Don't**

```bash
reboot
```

Right after editing fstab. A typo can stop the boot.

**Do instead**

```bash
mount -a && findmnt --verify
```

Test fstab now, while you can still fix it.

**5. Don't**

```bash
rm /var/log/app/huge.log
```

The space stays used while the app keeps the file open.

**Do instead**

```bash
truncate -s 0 /var/log/app/huge.log
```

Empty it instead. The space comes back at once.

## Explained

1. `dd if=ubuntu.iso of=/dev/sda`
   Writing an image to the wrong device overwrites it completely. sda and sdb are one letter apart. Instead: `lsblk -o NAME,SIZE,MODEL,MOUNTPOINT` first. The size and model tell you which disk is which. A mounted device is almost never the one you want to overwrite.

2. `mkfs.ext4 /dev/sdb1`
   Formatting is immediate. Pick the wrong partition and its data is gone. Instead: `blkid /dev/sdb1` before you format. If it already shows a filesystem type and a UUID, stop and find out what is on it.

3. `/dev/sdb1` in `/etc/fstab`
   Device names are assigned at boot and can change when disks are added or moved. Instead: use UUID= from blkid, and add nofail for data disks so a missing disk does not stop the server from booting.

4. Reboot right after editing fstab
   A single typo in fstab can drop the server into emergency mode at the next boot, far from SSH. Instead: `mount -a` to mount everything as the next boot would, and `findmnt --verify` to check the file for errors. Fix it now, not from a console at 2 AM.

5. rm on a huge log that is still open
   The file disappears from the folder, but the space stays used until the process closes it. Instead: `truncate -s 0` empties the file in place, and the space comes back immediately.

Before any disk command: `lsblk -f`. Five seconds, and you know exactly what you are about to touch.

## In one line

> **Look twice. Write once.** Disk commands do exactly what you type. There is no undo.

**Before any disk command**

```bash
lsblk -f
```
