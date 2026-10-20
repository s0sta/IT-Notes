---
id: p181
title: "Quiz: 3 RHCSA questions"
slug: quiz-3-rhcsa-questions
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, RHCSA, RHEL, SysAdmin, ITCareer]
source: "LinkedIn post P181 · Cloud / DevSecOps series"
linkedin_date: 2027-11-23
design: quiz
---

# Quiz: 3 RHCSA questions

RHCSA is the foundation of my Cloud/DevSecOps plan, because everything above it, Azure, Kubernetes, security, runs on Linux. Three questions that test whether the fundamentals are solid. Try each before the answer.

## Quick reference

**Q1. An app has perfect rwx permissions but still gets 'Permission denied' on RHEL. Why?**

- a) The disk is full
- b) SELinux is denying it
- c) The user is in too many groups

> **Answer:** b) SELinux is denying it. SELinux checks labels on top of normal permissions. `ls -Z` and ausearch reveal it; restorecon usually fixes it.

**Q2. Which command grows a logical volume and its filesystem in one step?**

- a) `lvextend -r`
- b) resize2fs
- c) vgextend

> **Answer:** a) `lvextend -r`. `lvextend -r` grows the LV and resizes the filesystem together. vgextend adds a disk to the group.

**Q3. You edited `/etc/fstab`. What do you run before rebooting?**

- a) systemctl daemon-reload
- b) `mount -a`
- c) `fsck -A`

> **Answer:** b) `mount -a`. `mount -a` mounts everything in fstab as boot would, so you catch a bad line now, not from a rescue console.

## Explained

1. An app has perfect rwx permissions but still gets Permission denied on RHEL. Why?

> **Answer:** SELinux is denying it. On RHEL-family systems, SELinux checks a security label on every file in addition to the normal permission bits, and it can deny an action that rwx would allow. `ls -Z` shows the context, `ausearch -m avc` shows the denial, and restorecon usually fixes it. Reaching for setenforce 0 only hides it.

2. Which command grows a logical volume and its filesystem in one step?

> **Answer:** `lvextend -r`. The -r resizes the filesystem on top at the same time as growing the logical volume, with no unmount and no downtime. vgextend is different: it adds a disk to the volume group. resize2fs resizes only the filesystem, `which lvextend -r` calls for you.

3. **You edited /etc/fstab.** What do you run before rebooting?

> **Answer:** `mount -a`. It mounts everything in fstab exactly as boot would, so a typo shows up as an error you can fix now, instead of dropping the server into emergency mode on the next reboot. `findmnt --verify` adds a sanity check.

All three are things you will actually do on real servers, which is the point of RHCSA: it is hands-on, not multiple choice.

## In one line

> **Fundamentals first. Then certs.** RHCSA is the base the whole cloud path stands on.

**Practise it:** break a VM, then fix it
