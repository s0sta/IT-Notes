---
id: p177
title: "Find risky file permissions with Python"
slug: find-risky-file-permissions-with-python
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, Linux, CyberSecurity, DevSecOps, SysAdmin]
source: "LinkedIn post P177 · Cloud / DevSecOps series"
linkedin_date: 2027-11-14
design: code
script: perms_audit.py
---

# Find risky file permissions with Python

Still in the Linux and security phase of my plan, here is a script that reflects exactly what RHCSA and CKS care about: permissions. It walks a folder and flags the classic risks, world-writable files, SUID and SGID binaries, and sensitive files like .env or keys that others can read. The full version is attached and uses only the standard library.

## Quick reference

The full script is at the end of this note: `perms_audit.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 perms_audit.py /var/www
```

**Example output**

```text
[!] world-writable /var/www/uploads/tmp
[FAIL] 1 risky item(s) found
```

## Explained

### Why it is useful

After a deploy, a careless chmod 777, or inheriting a server you did not set up, risky permissions hide in plain sight. This turns "I hope the perms are fine" into a short, specific list you can act on. It exits with code 1 when it finds something, so it also works as a CI gate before a release.

### What it checks

World-writable files and directories, which anyone on the box can overwrite. SUID and SGID binaries, which run with elevated rights and are a favourite for privilege escalation. And sensitive filenames that are readable by group or others, because a key only you should read is a key only you should read.

### How to use it

`python3 perms_audit.py /etc /home /var/www`. Run it on a schedule, or before going live, and compare the output over time. New findings are changes someone should be able to explain.

It is a first-line check, not a replacement for a full scanner or a CIS benchmark tool like kube-bench. But it is instant, portable, and catches the mistakes that cause real incidents.

## In one line

> **Audit before an attacker does.** A hardening check you can run in seconds, anywhere.

**Run it on a server**

```bash
python3 perms_audit.py /etc /home /var/www
```

## Script: perms_audit.py

Download: [scripts/perms_audit.py](../scripts/perms_audit.py)

```python
#!/usr/bin/env python3
"""perms_audit.py - find risky file permissions before an attacker does.

Walks a folder and flags the classics: world-writable files and directories,
SUID/SGID binaries, and sensitive files (.env, keys, .pem) that others can
read. A fast hardening check for any Linux server. Standard library only.

Usage:
    python3 perms_audit.py /var/www
    python3 perms_audit.py /etc /home

Exit code is 1 if anything risky is found.

By s0sta.com
"""
import os
import stat
import sys

SENSITIVE = (".env", ".pem", ".key", "id_rsa", "id_ed25519", ".htpasswd")


def main():
    roots = sys.argv[1:] or ["."]
    findings = 0
    for root in roots:
        for dirpath, dirs, files in os.walk(root):
            for name in files + dirs:
                path = os.path.join(dirpath, name)
                try:
                    mode = os.lstat(path).st_mode
                except OSError:
                    continue
                if stat.S_ISLNK(mode):
                    continue
                perm = stat.S_IMODE(mode)
                # world-writable
                if perm & stat.S_IWOTH:
                    findings += 1
                    print(f"[!] world-writable  {oct(perm)[-3:]}  {path}")
                # SUID / SGID
                if perm & (stat.S_ISUID | stat.S_ISGID) and os.path.isfile(path):
                    findings += 1
                    print(f"[!] SUID/SGID       {oct(perm)[-4:]}  {path}")
                # sensitive and readable by group/other
                if name.endswith(SENSITIVE) or name in SENSITIVE:
                    if perm & (stat.S_IRGRP | stat.S_IROTH):
                        findings += 1
                        print(f"[!] readable secret {oct(perm)[-3:]}  {path}")

    print(f"\n{'[FAIL]' if findings else '[OK]'} {findings} risky item(s) found")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
```
