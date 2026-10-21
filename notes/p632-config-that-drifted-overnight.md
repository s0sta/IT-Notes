---
id: p632
title: "Config that drifted overnight"
slug: config-that-drifted-overnight
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, DevSecOps, ConfigManagement, SRE]
source: "LinkedIn post P632 · ShellSec series"
linkedin_date: 2030-10-10
design: code
script: config_drift.sh
---

# Config that drifted overnight

At 02:40 the deploy key stops working. The sshd config differs from Git by one line, and nobody opened a change request.

## Quick reference

The full script is at the end of this note: `config_drift.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash config_drift.sh /var/lib/etc-base /etc
```

**Example output**

```text
FINDING 2 files drifted
CHANGED ssh/sshd_config
```

## Explained

### What it does

`config_drift.sh` hashes every regular file in a live tree and compares it with a baseline copy or tarball. A file is CHANGED when the hash differs, ADDED when only the live tree has it, and REMOVED when only the baseline does.

### What the screen shows

The fourteen lines hash each live file, write ADDED and CHANGED lines to a temp list, then print the count and the first path. On the fixture: FINDING 2 files drifted and CHANGED ssh/sshd_config. The script also walks the baseline for REMOVED files.

### How to run it

bash `config_drift.sh -b /var/lib/s0sta/etc-baseline -r /etc`. The cron line is 15 3 \* \* \* and the log is `/var/log/s0sta/config-drift.log`. Exit 0 is clean, 1 is drift, 2 is a bad path or unreadable baseline.

### The fix

Diff the named file against the baseline, then Git. If it was a hotfix, commit it and re-baseline; if not, restore it and find the session that wrote it. An ADDED file in sshd_config.d matters most: it changes behaviour without touching the main file.

### Prevention

Re-baseline after every approved change, in the same pull request. A baseline taken once and never refreshed becomes a finding everyone ignores.

> **The honest caveat:** a hash proves the file changed, not who changed it. Pair it with auditd.

> **The lesson:** drift is not a mysterious force. It is a file, a time and a person.

## In one line

> **The file changed. Nobody did it.** A baseline turns an unseen edit into a named file and a line.

**Diff the tree:** `config_drift.sh -b /var/lib/etc-base`

## Script: config_drift.sh

Download: [scripts/config_drift.sh](../scripts/config_drift.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
#
# config_drift.sh - report config files that changed against a baseline.
#
# Fixes: config that drifted overnight. Every regular file under --root is
# compared with a baseline directory, or with a tarball made like this:
#   tar -C /etc -czf /var/lib/s0sta/etc-baseline.tgz .
# A file is CHANGED when its SHA-256 differs, ADDED when only the live tree
# has it, and REMOVED when only the baseline has it. Read-only: the target
# tree is never written to.
#
# Usage:
#   config_drift.sh --baseline /var/lib/s0sta/etc-baseline
#   config_drift.sh -b /var/lib/s0sta/etc-baseline -r /etc
#   config_drift.sh -b /var/lib/s0sta/etc-baseline.tgz -r /etc
#   config_drift.sh --help
#
# Cron (03:15 daily; exit 1 means drift):
#   15 3 * * * /usr/local/sbin/config_drift.sh -b /var/lib/s0sta/etc \
#     >>/var/log/s0sta/config-drift.log 2>&1
#
# Exit: 0 no drift, 1 drift found, 2 usage or unreadable input.
# Needs: sha256sum, or shasum -a 256 on macOS/BSD; tar for a tarball baseline.
# By s0sta.com
#
usage() {
    cat <<'EOF'
config_drift.sh - report config drift against a baseline copy.

Usage:
  config_drift.sh --baseline DIR|TARBALL [--root DIR]
  config_drift.sh -b DIR -r /etc

  -b, --baseline PATH  baseline directory (a copy of the tree) or .tar/.tgz
  -r, --root DIR       live tree to inspect (default: /etc)
  -h, --help           show this help and exit 0

Exit: 0 no drift, 1 drift found, 2 usage or unreadable input.
Read-only: the live tree is never modified.
EOF
}

die() {
    printf 'config_drift: %s\n' "$1" >&2
    exit 2
}

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" 2>/dev/null | cut -d' ' -f1
    else
        shasum -a 256 "$1" 2>/dev/null | cut -d' ' -f1
    fi
}

list_tree() {
    ( cd "$1" && find . -type f -print ) | sed 's|^\./||' | LC_ALL=C sort
}

ROOT=/etc
BASE=
while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        -b|--baseline)
            [ "$#" -ge 2 ] || die "--baseline needs a path"
            BASE=$2; shift 2 ;;
        -r|--root)
            [ "$#" -ge 2 ] || die "--root needs a path"
            ROOT=$2; shift 2 ;;
        *) die "unknown argument: $1" ;;
    esac
done

[ -n "$BASE" ] || die "missing --baseline"
[ -d "$ROOT" ] || die "not a directory: $ROOT"
[ -r "$ROOT" ] || die "cannot read: $ROOT"
if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
    die "need sha256sum or shasum"
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/config_drift.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

if [ -d "$BASE" ]; then
    BDIR=$BASE
elif [ -f "$BASE" ]; then
    mkdir -p "$TMP/base"
    tar -xf "$BASE" -C "$TMP/base" 2>/dev/null || die "cannot unpack: $BASE"
    BDIR=$TMP/base
else
    die "baseline not found: $BASE"
fi

list_tree "$BDIR" >"$TMP/base.list"
list_tree "$ROOT" >"$TMP/live.list"
comm -12 "$TMP/base.list" "$TMP/live.list" >"$TMP/common.list"
comm -13 "$TMP/base.list" "$TMP/live.list" >"$TMP/added.list"
comm -23 "$TMP/base.list" "$TMP/live.list" >"$TMP/removed.list"

: >"$TMP/changed.list"
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    if [ "$(hash_file "$BDIR/$rel")" != "$(hash_file "$ROOT/$rel")" ]; then
        printf '%s\n' "$rel" >>"$TMP/changed.list"
    fi
done <"$TMP/common.list"

CHANGED=$(wc -l <"$TMP/changed.list" || true)
ADDED=$(wc -l <"$TMP/added.list" || true)
REMOVED=$(wc -l <"$TMP/removed.list" || true)
TOTAL=$((CHANGED + ADDED + REMOVED))

if [ "$TOTAL" -eq 0 ]; then
    FILES=$(wc -l <"$TMP/live.list" || true)
    printf 'OK no drift against %s (%d files)\n' "$BASE" "$FILES"
    exit 0
fi

printf 'FINDING %d files drifted\n' "$TOTAL"
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    printf 'CHANGED %s\n' "$rel"
done <"$TMP/changed.list"
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    printf 'ADDED %s\n' "$rel"
done <"$TMP/added.list"
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    printf 'REMOVED %s\n' "$rel"
done <"$TMP/removed.list"

exit 1
```
