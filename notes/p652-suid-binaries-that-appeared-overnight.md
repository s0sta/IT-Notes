---
id: p652
title: "SUID binaries that appeared overnight"
slug: suid-binaries-that-appeared-overnight
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, CyberSecurity, DevSecOps, SysAdmin]
source: "LinkedIn post P652 · ShellSec series"
linkedin_date: 2030-11-26
design: code
script: suid_watch.sh
---

# SUID binaries that appeared overnight

At 04:12 a setuid binary appears in `/usr/local/bin`. It is root-owned, world-executable, and nobody remembers installing it. The file is newer than the last deploy, the only clue the box offers.

## Quick reference

The full script is at the end of this note: `suid_watch.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
SUID_BASELINE=/tmp/s0f/suid.base bash suid_watch.sh /tmp/s0f/root
```

**Example output**

```text
FINDING 1 new SUID/SGID files
NEW 4755 root:root /tmp/s0f/root/bin/passwd.old
```

## Explained

### What it does

`suid_watch.sh` sweeps a root with `find -xdev`, keeps every file with -perm -4000 or -2000, and prints mode, owner and path, sorted. `--update` writes that set as the baseline. A check run diffs both sides with comm, reports new and removed, and exits 1 only when something is new.

### What the screen shows

The fourteen lines read SUID_BASELINE, sweep the root, write the set to a temp file and diff it. On the dirty fixture: FINDING 1 new SUID/SGID files and NEW 4755 root:root `/tmp/s0f/root/bin/passwd.old`.

### How to run it

`sudo suid_watch.sh --update /` once, then run it from cron at 04:10. Exit 0 is clean or only removals, 1 is a new setuid or setgid file, 2 is a missing baseline or bad argument. It writes only the baseline.

### The fix

A new setuid file is an unexpected package or an intruder. Run `dpkg -S` or `rpm -qf` on the path; if nothing owns it, move it aside and keep a copy for forensics. Clear it with chmod u-s or g-s.

### Prevention

Keep the baseline in git and review each `--update`. A setuid bit is a root shell waiting for a bug, so keep it short.

> **The honest caveat:** find skips unreadable subtrees, so run the sweep as root.

> **The lesson:** a baseline turns "what is this file" into "who changed it".

## In one line

> **A new bit is a new door.** Setuid is a root shell waiting for a bug. Keep the list short.

**Build the baseline**

```bash
sudo suid_watch.sh --update /
```

## Script: suid_watch.sh

Download: [scripts/suid_watch.sh](../scripts/suid_watch.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
# suid_watch.sh - baseline SUID/SGID files and report the delta.
#
# Fixes: a root-owned setuid binary appears overnight and nobody notices
# until it is used. The sweep compares the current setuid/setgid set with
# an approved baseline, so the question changes from "what is this file"
# to "who changed the baseline".
#
# Usage:
#   sudo ./suid_watch.sh --update /            # write the baseline
#   sudo ./suid_watch.sh /                     # check against it
#   ./suid_watch.sh -b ./suid.base -r /usr -r /opt
#
# Cron (daily, 04:10):
#   10 4 * * * root /usr/local/sbin/suid_watch.sh / >> /var/log/suid_watch.log 2>&1
#
# Exit: 0 clean or only removals, 1 new SUID/SGID file, 2 usage or unreadable
# input. Requires GNU find (-printf). Unreadable subtrees are skipped, so run
# as root for a complete sweep. SUID_BASELINE overrides the default baseline
# path. Check mode writes nothing; --update writes the baseline file only.
#
# By s0sta.com

IFS=$'\n\t'

BASELINE=${SUID_BASELINE:-/var/lib/s0sta/suid.baseline}
MODE=check
ROOTS=()

usage() {
  cat <<'EOF'
Usage: suid_watch.sh [options] [ROOT...]

Build or check a baseline of SUID and SGID files.

Options:
  -b, --baseline FILE   baseline to read or write
                        (default: /var/lib/s0sta/suid.baseline)
  -u, --update          write the current sweep as the new baseline
  -r, --root PATH       root to scan; repeatable (default: /)
  -h, --help            show this help and exit

SUID_BASELINE overrides the default baseline path.
Exit: 0 clean or only removals, 1 new SUID/SGID file, 2 usage or unreadable input.
By s0sta.com
EOF
}

die() {
  printf 'ERROR %s\n' "$1" >&2
  exit 2
}

scan() {
  local root
  for root in "${ROOTS[@]}"; do
    find "$root" -xdev -type f \( -perm -4000 -o -perm -2000 \) \
      -printf '%m %u:%g %p\n' 2>/dev/null || true
  done | LC_ALL=C sort -u
}

emit() {
  if [ -n "$1" ]; then
    printf '%s\n' "$1"
  fi
}

count_lines() {
  if [ -z "$1" ]; then
    printf '0\n'
  else
    printf '%s\n' "$1" | awk 'NF { n++ } END { print n + 0 }'
  fi
}

while [ "$#" -gt 0 ]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    -b|--baseline)
      [ "$#" -ge 2 ] || die "$1 needs a file"
      BASELINE=$2
      shift 2
      ;;
    -u|--update)
      MODE=update
      shift
      ;;
    -r|--root)
      [ "$#" -ge 2 ] || die "$1 needs a path"
      ROOTS+=("$2")
      shift 2
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        ROOTS+=("$1")
        shift
      done
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      ROOTS+=("$1")
      shift
      ;;
  esac
done

if [ "${#ROOTS[@]}" -eq 0 ]; then
  ROOTS=(/)
fi

for root in "${ROOTS[@]}"; do
  [ -d "$root" ] || die "not a directory: $root"
done

if [ "$MODE" = "update" ]; then
  base_dir=${BASELINE%/*}
  if [ "$base_dir" = "$BASELINE" ]; then
    base_dir=.
  fi
  if [ ! -d "$base_dir" ]; then
    mkdir -p "$base_dir" || die "cannot create $base_dir"
  fi
  tmp=$(mktemp "${BASELINE}.XXXXXX") || die "cannot create a temp file next to $BASELINE"
  trap 'rm -f "$tmp"' EXIT
  scan > "$tmp"
  chmod 0644 "$tmp" 2>/dev/null || true
  mv "$tmp" "$BASELINE" || die "cannot write baseline: $BASELINE"
  trap - EXIT
  entries=$(awk 'END { print NR + 0 }' "$BASELINE")
  printf 'BASELINE %s %s entries\n' "$BASELINE" "$entries"
  exit 0
fi

if [ ! -f "$BASELINE" ]; then
  die "baseline missing: $BASELINE (run with --update)"
fi
[ -r "$BASELINE" ] || die "cannot read baseline: $BASELINE"

base_sorted=$(LC_ALL=C sort -u "$BASELINE")
current=$(scan)
new=$(comm -13 <(emit "$base_sorted") <(emit "$current") || true)
removed=$(comm -23 <(emit "$base_sorted") <(emit "$current") || true)

new_n=$(count_lines "$new")
rem_n=$(count_lines "$removed")

if [ "$new_n" -eq 0 ] && [ "$rem_n" -eq 0 ]; then
  entries=$(awk 'END { print NR + 0 }' "$BASELINE")
  printf 'OK baseline matches: %s entries\n' "$entries"
  exit 0
fi

if [ "$new_n" -gt 0 ]; then
  printf 'FINDING %d new SUID/SGID files\n' "$new_n"
  printf '%s\n' "$new" | sed 's/^/NEW /'
fi

if [ "$rem_n" -gt 0 ]; then
  printf 'REMOVED %d baseline entries\n' "$rem_n"
  printf '%s\n' "$removed" | sed 's/^/GONE /'
fi

if [ "$new_n" -gt 0 ]; then
  exit 1
fi

exit 0
```
