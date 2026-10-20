---
id: p180
title: "The layers that decide who can touch a file on RHEL"
slug: the-layers-that-decide-who-can-touch-a-file-on-rhel
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, RHEL, SELinux, RHCSA, SysAdmin]
source: "LinkedIn post P180 · Cloud / DevSecOps series"
linkedin_date: 2027-11-21
design: stack
---

# The layers that decide who can touch a file on RHEL

On RHEL, "can this user open this file?" is answered by several layers stacked on top of each other, and access is granted only if every one of them agrees. Understanding the stack explains the most confusing permission errors.

## Quick reference

*Bottom to top: each layer can still say no*

1. **The user and groups** — Who you are, and which groups you belong to. · `id`
2. **File ownership** — Every file has an owner and a group. · `chown`
3. **Permission bits** — The rwx for owner, group and others. · `chmod`
4. **ACLs** — Extra per-user or per-group rules beyond the basics. · `setfacl`
5. **SELinux** — Labels and policy, checked even when rwx allows it. · `ls -Z`
6. **The result** — Access is granted only if every layer agrees. · `allow / deny`

## Explained

The user and groups. It starts with identity: your user ID and the groups you belong to, which id shows. Group membership is why adding someone to a group can grant access, but only after they log in again.

File ownership. Every file has an owner and a group, set with chown. The permission check depends on whether you are the owner, in the group, or neither.

Permission bits. The familiar rwx for owner, group and others, set with chmod. This is the layer most people stop at, and most of the time it is the answer.

ACLs. When the basic three are not enough, Access Control Lists add extra rules for specific users or groups with setfacl and getfacl. A small + at the end of `ls -l` output means a file has ACLs.

SELinux. On top of all of that, SELinux checks labels and policy. It can deny an action even when the ownership, bits and ACLs would allow it. This is why a file with perfect rwx can still give Permission denied.

The result. Access is granted only if every layer agrees. Any one of them can say no.

> **The debugging order that works:** when rwx looks correct and it still fails, go up the stack. Check `ls -Z` for the SELinux context and getfacl for ACLs, not just `ls -l`.

## In one line

> **Every layer can still say no.** 'Permission denied' with perfect rwx usually means SELinux.

**Check top-down**

```bash
ls -Z; getfacl file; ls -l
```
