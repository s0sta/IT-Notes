---
id: p176
title: "Fix: the app works with SELinux off, fails with it on"
slug: fix-the-app-works-with-selinux-off-fails-with-it-on
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, SELinux, RHEL, Troubleshooting, RHCSA]
source: "LinkedIn post P176 · Cloud / DevSecOps series"
linkedin_date: 2027-11-11
design: steps
---

# Fix: the app works with SELinux off, fails with it on

Every RHEL admin meets this moment: the app fails, someone runs setenforce 0, it works, and SELinux gets blamed and left off. That is not a fix. It switches off a real security layer to avoid fixing one label. Here is the proper way.

## Quick reference

### Diagnose — Confirm it is SELinux

```bash
# If it works now, SELinux is the cause. Turn it back on.
setenforce 0  (test only!)
# The denial names the process, action and context.
ausearch -m avc -ts recent
# Wrong context? default_t instead of an app type.
ls -Z /srv/app/uploads
```

### Fix — Give the path the right label

```bash
# Set the correct default context.
semanage fcontext -a -t <web_rw_type> '/srv/app(/.*)?'
# Apply it to the existing files.
restorecon -Rv /srv/app/uploads
# Back to Enforcing. Test again: it should pass.
setenforce 1
```

### Prevent — Work with SELinux, not against it

- `audit2why < /var/log/audit/audit.log` — Explains a denial in plain language.
- **Check booleans first** — `getsebool -a` often has the toggle you need.
- **Label new paths up front** — Add fcontext rules when you deploy, not after.

## Explained

### Diagnose

setenforce 0 is fine as a one-minute test: if the problem disappears, SELinux is involved. Then `setenforce 1` immediately, because leaving it off is the mistake.  
`ausearch -m avc -ts recent` shows the denial: which process, which action (read, write, connect) and the context it was denied. This is your evidence.  
`ls -Z` on the path usually reveals the issue: files sitting with a generic type like default_t instead of the type the service is allowed to use.

### Fix

`semanage fcontext -a -t` ... sets the correct default context for the path. For a writable app folder served by the web server, that is often httpd_sys_rw_content_t.  
`restorecon -Rv` applies that label to the files already there.  
`setenforce 1` returns to Enforcing, and the app now works with SELinux fully on.

### Prevent

audit2why reads a denial and explains it in plain language, often suggesting the exact fix.  
Check booleans first: `getsebool -a` frequently has a ready-made toggle, like letting the web server connect to a database.  
Label new paths when you deploy, not after they break.

The mindset shift: SELinux is not in your way, it is telling you a label is wrong. Fix the label and you keep both the app and the protection.

## In one line

> **setenforce 0 is not a fix.** It switches off a whole security layer to hide one label.

**The real fix**

```bash
semanage fcontext + restorecon
```
