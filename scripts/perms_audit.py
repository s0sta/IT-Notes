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
