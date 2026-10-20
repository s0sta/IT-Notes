---
id: p173
title: "9 SELinux commands that fix Permission denied"
slug: 9-selinux-commands-that-fix-permission-denied
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, RHEL, SELinux, RHCSA, SysAdmin]
source: "LinkedIn post P173 · Cloud / DevSecOps series"
linkedin_date: 2027-11-04
design: terminal
---

# 9 SELinux commands that fix Permission denied

On RHEL and its family, the most confusing error is the one where the file permissions look perfect and the app still gets Permission denied. The usual culprit is SELinux, and the RHCSA exam expects you to handle it. Nine commands that turn it from a mystery into a routine.

## Quick reference

### Is SELinux the cause?

```bash
# Enforcing means SELinux can block things
getenforce
# -Z shows the security context, the key field
ls -Z /var/www/html
# the actual denials, in plain-ish text
ausearch -m avc -ts recent
```

### Fix the context

```bash
# reset files to their correct default context
restorecon -Rv /var/www
# set a new default context for a path
semanage fcontext -a -t httpd_sys_rw_content_t '/srv/app(/.*)?'
# change one file's context (temporary, test only)
chcon -t httpd_sys_content_t file.html
```

### Booleans and ports

```bash
# toggles for common app behaviour
getsebool -a | grep httpd
# -P makes it permanent. Let the app reach the DB
setsebool -P httpd_can_network_connect on
# let a service listen on a non-standard port
semanage port -a -t http_port_t -p tcp 8080
```

## Explained

### Is SELinux the cause?

`getenforce` tells you if it is Enforcing, Permissive or Disabled. In Enforcing mode it can block actions that normal permissions would allow.  
`ls -Z` shows the security context of files, the part normal ls hides. The context, not just rwx, decides what a labelled service may touch.  
`ausearch -m avc -ts recent` lists the actual denials. This is the evidence, and it usually names the fix.

### Fix the context

`restorecon -Rv` resets files to their correct default context. This single command solves a huge share of SELinux problems, especially after moving files into a web root.  
semanage fcontext adds a new default context for a path, so it survives a relabel. Pair it with restorecon.  
chcon changes one file's context immediately, but it is not permanent, so use it only to test a theory.

### Booleans and ports

getsebool and `setsebool -P` toggle built-in behaviours, like letting the web server make network connections. The -P makes it stick across reboots.  
semanage port lets a service listen on a non-standard port, like nginx on 8080.

> **The one habit that matters:** do not reach for setenforce 0. Turning SELinux off hides the problem and removes a real layer of defence. Read the denial, fix the label.

## In one line

> **Don't disable it. Label it.** setenforce 0 hides the problem. restorecon fixes it.

**Try it**

```bash
ausearch -m avc -ts recent
```
