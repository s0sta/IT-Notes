---
id: p656
title: "ACLs that override your permissions"
slug: acls-that-override-your-permissions
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, CyberSecurity, AccessControl, SysAdmin]
source: "LinkedIn post P656 · ShellSec series"
linkedin_date: 2030-12-05
design: code
script: acl_audit.sh
---

# ACLs that override your permissions

A deploy user needs to write one directory. Six months later getfacl shows three named groups with rwx, a default ACL on the parent, and a mode that looks harmless in ls.

## Quick reference

The full script is at the end of this note: `acl_audit.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash acl_audit.sh /tmp/s0f/acl.dump
```

**Example output**

```text
WRITE /srv/app group:contractors:rwx
FINDING 1 ACL risks
```

## Explained

### What it does

`acl_audit.sh` reads a `getfacl -R` dump, or runs getfacl on the paths you give it, and walks each file block. It flags named users and groups whose effective permissions include write, other:: with write, any default ACL, and named entries that grant a bit the base class does not have.

### What the screen shows

The thirteen lines read the dump, print one line per risk and exit 1 when the count is above zero. On the dirty fixture: WRITE `/srv/app group:contractors:rwx` and FINDING 1 ACL risks.

### How to run it

`acl_audit.sh acl.dump` for an offline review, or `acl_audit.sh /srv /etc` for a live sweep. Exit 0 is clean, 1 is a risk, 2 is a missing path or no getfacl.

### The fix

Remove the entry with `setfacl -x g:contractors /srv/app`, or reduce it with `setfacl -m g:contractors:r-x`. A default ACL needs a decision; `setfacl -k` removes it. Then chmod back to the mode you meant, because the mask follows.

### Prevention

Review ACL changes beside the chmod. A weekly dump diff catches the entry added to unblock a deploy and never removed.

> **The honest caveat:** a read-only ACL entry is invisible in `ls -l`, and this script looks for write.

> **The lesson:** the mode is a summary; the ACL is the access list.

## In one line

> **The mode is not the whole story.** A named entry can grant what `ls -l` never shows.

**Dump the acls**

```bash
getfacl -R -p /srv > acl.dump
```

## Script: acl_audit.sh

Download: [scripts/acl_audit.sh](../scripts/acl_audit.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
# acl_audit.sh - find risky POSIX ACLs in a getfacl dump or a live tree.
#
# Fixes: a deploy user gets rwx on one directory, the ACL is never removed,
# and ls -l still shows a harmless mode. The script flags named entries with
# effective write, other:: with write, default ACLs, and named entries that
# widen the base class.
#
# Usage:
#   ./acl_audit.sh /srv /etc
#   getfacl -R -p /srv > acl.dump && ./acl_audit.sh acl.dump
#
# Cron (weekly, Monday 06:20):
#   20 6 * * 1 root /usr/local/sbin/acl_audit.sh /srv /etc >> /var/log/acl_audit.log 2>&1
#
# Exit: 0 clean, 1 risky ACL, 2 usage or unreadable input.
# A directory is scanned with getfacl -R -p (GNU acl package); a regular file is
# parsed as a saved dump, so the check also runs on a host without getfacl.
# The mask is applied before write is called effective. Reads only.
#
# By s0sta.com

IFS=$'\n\t'

PATHS=()
WORK=""

usage() {
  cat <<'EOF'
Usage: acl_audit.sh [options] [PATH...]

Audit POSIX ACLs from a live tree or a saved getfacl dump.

Options:
  -h, --help   show this help and exit

A directory is scanned with getfacl -R -p; a regular file is read as a saved
dump. With no PATH, the usual service directories are used.

Exit: 0 clean, 1 risky ACL, 2 usage or unreadable input.
By s0sta.com
EOF
}

die() {
  printf 'ERROR %s\n' "$1" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        PATHS+=("$1")
        shift
      done
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      PATHS+=("$1")
      shift
      ;;
  esac
done

if [ "${#PATHS[@]}" -eq 0 ]; then
  for p in /etc /srv /opt /var/www; do
    if [ -d "$p" ]; then
      PATHS+=("$p")
    fi
  done
fi

if [ "${#PATHS[@]}" -eq 0 ]; then
  printf 'SKIP no paths to audit\n'
  exit 0
fi

WORK=$(mktemp -d "${TMPDIR:-/tmp}/acl_audit.XXXXXX") || die "cannot create a work directory"
trap 'rm -rf "$WORK"' EXIT
DUMP=$WORK/acl.dump
: > "$DUMP"

for p in "${PATHS[@]}"; do
  if [ -d "$p" ]; then
    command -v getfacl >/dev/null 2>&1 || die "getfacl not installed: pass a saved dump instead"
    if ! getfacl -R -p "$p" >> "$DUMP" 2>/dev/null; then
      printf 'NOTE getfacl reported errors on %s\n' "$p" >&2
    fi
  elif [ -f "$p" ]; then
    [ -r "$p" ] || die "cannot read $p"
    cat "$p" >> "$DUMP"
  else
    die "not a file or directory: $p"
  fi
done

if [ ! -s "$DUMP" ]; then
  printf 'SKIP no ACL data\n'
  exit 0
fi

status=0
awk '
  function eff(p, m,   e, i, c) {
    e = ""
    for (i = 1; i <= 3; i++) {
      c = substr("rwx", i, 1)
      if (index(p, c) && (m == "" || index(m, c))) e = e c
      else e = e "-"
    }
    return e
  }
  function extra(e, b,   x) {
    x = ""
    if (index(e, "r") && !index(b, "r")) x = x "r"
    if (index(e, "w") && !index(b, "w")) x = x "w"
    if (index(e, "x") && !index(b, "x")) x = x "x"
    return x
  }
  function flush(   i, e, x) {
    if (f == "") return
    if (def != "") {
      printf "DEFAULT %s %s\n", f, def
      n++
    }
    for (i = 1; i <= nu; i++) {
      e = eff(u_perm[i], mask)
      if (index(e, "w")) {
        printf "WRITE %s user:%s=%s\n", f, u_name[i], e
        n++
      } else {
        x = extra(e, u_base)
        if (x != "") {
          printf "WIDEN %s user:%s=%s base=%s\n", f, u_name[i], e, u_base
          n++
        }
      }
    }
    for (i = 1; i <= ng; i++) {
      e = eff(g_perm[i], mask)
      if (index(e, "w")) {
        printf "WRITE %s group:%s=%s\n", f, g_name[i], e
        n++
      } else {
        x = extra(e, g_base)
        if (x != "") {
          printf "WIDEN %s group:%s=%s base=%s\n", f, g_name[i], e, g_base
          n++
        }
      }
    }
    if (index(o_perm, "w")) {
      printf "OTHER %s other::%s\n", f, o_perm
      n++
    }
    f = ""; def = ""; u_base = ""; g_base = ""; o_perm = ""; mask = ""
    nu = 0; ng = 0
  }
  /^# file: / {
    flush()
    f = substr($0, 9)
    next
  }
  /^#/ { next }
  /^default:/ {
    def = (def == "" ? $0 : def " | " $0)
    next
  }
  {
    line = $0
    sub(/[ \t]*#.*/, "", line)
    if (line !~ /^(user|group|mask|other):/) next
    split(line, p, ":")
    who = p[1]
    name = p[2]
    perms = p[3]
    if (who == "mask") { mask = perms; next }
    if (who == "other") { o_perm = perms; next }
    if (name == "") {
      if (who == "user") u_base = perms
      else g_base = perms
      next
    }
    if (who == "user") {
      nu++
      u_name[nu] = name
      u_perm[nu] = perms
    } else {
      ng++
      g_name[ng] = name
      g_perm[ng] = perms
    }
  }
  END {
    flush()
    if (n == 0) {
      print "OK no risky ACLs"
      exit 0
    }
    printf "FINDING %d ACL risks\n", n
    exit 1
  }
' "$DUMP" || status=$?
exit "$status"
```
