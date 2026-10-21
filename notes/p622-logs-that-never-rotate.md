---
id: p622
title: "Logs that never rotate"
slug: logs-that-never-rotate
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, SysAdmin, DevOps, Automation]
source: "LinkedIn post P622 · ShellSec series"
linkedin_date: 2030-09-17
design: code
script: log_rotate_check.sh
---

# Logs that never rotate

A 40 GB log partition fills at 03:40, and every service that writes to it fails. logrotate is installed, its configuration is valid, and the file that grew has no matching stanza.

## Quick reference

The full script is at the end of this note: `log_rotate_check.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash log_rotate_check.sh /tmp/p622/logs
```

**Example output**

```text
FINDING 2 flags in /tmp/p622/logs
ALERT /tmp/p622/logs/app.log 3104MB over 100MB
```

## Explained

### What it does

`log_rotate_check.sh` walks directories and applies three limits: a `file over --max-mb (100` by default), a file untouched for `--max-days (30`), and a directory over `--dir-budget (1024` MB). It prints a FINDING line, an ALERT for the worst item and one logrotate stanza. It reads metadata only and changes nothing.

### What the screen shows

The fourteen lines count files over the size limit and older than 30 days, then print the summary and the largest offender. On the fixture: FINDING 2 flags in `/tmp/p622/logs` and ALERT `/tmp/p622/logs/app.log 3104MB` over 100MB.

### How to run it

bash `log_rotate_check.sh --max-mb 200 /var/log`. Exit 0 is clean, 1 a finding, 2 usage or an unreadable directory. The cron line is `0 6 * * * /usr/local/bin/log_rotate_check.sh /var/log`.

### The fix

Give the file a size stanza: size 200M, rotate 30, compress. Give the quiet directory a time policy. Rotate before you delete, because rotation keeps the last copy and a delete keeps nothing. Then cap the producer that writes without a bound.

### Prevention

Run the check daily and alert on exit 1. Keep `--dir-budget` below the filesystem's real capacity, and check inodes with `df -i`.

> **The honest caveat:** the script measures the tree you point it at; a log written to journald or a socket never appears.

> **The lesson:** a full disk is usually a policy failure, not a storage failure.

## In one line

> **The disk fills by policy.** Rotation is a policy you write before the disk is full.

**Check the tree:** bash `log_rotate_check.sh /var/log`

## Script: log_rotate_check.sh

Download: [scripts/log_rotate_check.sh](../scripts/log_rotate_check.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# log_rotate_check.sh - find the logs that will fill the disk before they do.
# Fixes: a file over --max-mb, a file untouched for --max-days, and a directory
#        over --dir-budget. Read-only: prints findings and one logrotate stanza,
#        changes nothing.
#
# Usage:
#   log_rotate_check.sh [options] DIR [DIR...]
#   log_rotate_check.sh --max-mb 200 --max-days 14 /var/log
#
# Options:
#   --max-mb N      flag files larger than N MiB (default 100)
#   --max-days N    flag files older than N days (default 30)
#   --dir-budget N  flag directories over N MiB (default 1024)
#   --top N         show at most N details per class (default 5)
#   -h, --help      show this help and exit 0
#
# Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
# Needs: GNU findutils, coreutils (find, stat, du, sort), awk. Linux.
# Cron: 0 6 * * * /usr/local/bin/log_rotate_check.sh /var/log
# By s0sta.com

usage() {
    cat <<'EOF'
log_rotate_check.sh - find the logs that will fill the disk before they do.

Usage:
  log_rotate_check.sh [options] DIR [DIR...]
  log_rotate_check.sh --max-mb 200 --max-days 14 /var/log

Options:
  --max-mb N      flag files larger than N MiB (default 100)
  --max-days N    flag files older than N days (default 30)
  --dir-budget N  flag directories over N MiB (default 1024)
  --top N         show at most N details per class (default 5)
  -h, --help      show this help and exit 0

Read-only. Prints one suggested logrotate stanza per directory.
Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
EOF
}

die() {
    printf 'ERROR %s\n' "$*" >&2
    exit 2
}

is_number() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

max_mb=100
max_days=30
budget_mb=1024
top=5
dirs=()

while [ "$#" -gt 0 ]; do
    case "$1" in
        --max-mb)       [ "$#" -ge 2 ] || die "missing value for $1"; max_mb=$2; shift 2 ;;
        --max-days)     [ "$#" -ge 2 ] || die "missing value for $1"; max_days=$2; shift 2 ;;
        --dir-budget)   [ "$#" -ge 2 ] || die "missing value for $1"; budget_mb=$2; shift 2 ;;
        --top)          [ "$#" -ge 2 ] || die "missing value for $1"; top=$2; shift 2 ;;
        -h|--help)      usage; exit 0 ;;
        --)             shift; while [ "$#" -gt 0 ]; do dirs+=("$1"); shift; done ;;
        -*)             die "unknown option: $1 (try --help)" ;;
        *)              dirs+=("$1"); shift ;;
    esac
done

for value in "$max_mb" "$max_days" "$budget_mb" "$top"; do
    is_number "$value" || die "not a number: $value"
done
[ "${#dirs[@]}" -gt 0 ] || die "no directory given (try --help)"
for dir in "${dirs[@]}"; do
    [ -d "$dir" ] || die "not a directory: $dir"
    [ -r "$dir" ] || die "unreadable directory: $dir"
done

if stat -c %s / >/dev/null 2>&1; then
    STAT_STYLE=gnu
else
    STAT_STYLE=bsd
fi

size_bytes() {
    if [ "$STAT_STYLE" = gnu ]; then
        stat -c %s -- "$1" 2>/dev/null || printf '0'
    else
        stat -f %z -- "$1" 2>/dev/null || printf '0'
    fi
}

mtime_epoch() {
    if [ "$STAT_STYLE" = gnu ]; then
        stat -c %Y -- "$1" 2>/dev/null || printf '0'
    else
        stat -f %m -- "$1" 2>/dev/null || printf '0'
    fi
}

now=$(date +%s)
total=0

for dir in "${dirs[@]}"; do
    big_count=0
    old_count=0
    budget_hit=0
    big_list=()
    old_list=()
    biggest=""
    biggest_size=0
    oldest=""
    oldest_days=0

    while IFS= read -r -d '' file; do
        big_count=$((big_count + 1))
        bytes=$(size_bytes "$file")
        big_list+=("$bytes"$'\t'"$file")
        if [ "$bytes" -gt "$biggest_size" ]; then
            biggest=$file
            biggest_size=$bytes
        fi
    done < <(find "$dir" -type f -size +"${max_mb}"M -print0 2>/dev/null)

    while IFS= read -r -d '' file; do
        old_count=$((old_count + 1))
        mtime=$(mtime_epoch "$file")
        days=$(( (now - mtime) / 86400 ))
        old_list+=("$days"$'\t'"$file")
        if [ "$days" -gt "$oldest_days" ]; then
            oldest=$file
            oldest_days=$days
        fi
    done < <(find "$dir" -type f -mtime +"${max_days}" -print0 2>/dev/null)

    dir_mb=$(du -sm "$dir" 2>/dev/null | awk '{print $1}')
    dir_mb=${dir_mb:-0}
    if [ "$dir_mb" -gt "$budget_mb" ]; then
        budget_hit=1
    fi

    flags=$((big_count + old_count + budget_hit))
    total=$((total + flags))
    if [ "$flags" -eq 1 ]; then
        label=flag
    else
        label=flags
    fi
    printf 'FINDING %d %s in %s\n' "$flags" "$label" "$dir"

    alert=""
    skip_big=""
    skip_old=""
    if [ "$biggest_size" -gt 0 ]; then
        alert=big
        skip_big=$biggest
    elif [ "$oldest_days" -gt 0 ]; then
        alert=old
        skip_old=$oldest
    elif [ "$budget_hit" -eq 1 ]; then
        alert=budget
    fi

    if [ "$alert" = big ]; then
        biggest_mb=$((biggest_size / 1048576))
        printf 'ALERT %s %dMB over %dMB\n' "$biggest" "$biggest_mb" "$max_mb"
    elif [ "$alert" = old ]; then
        printf 'ALERT %s %dd untouched (max %dd)\n' "$oldest" "$oldest_days" "$max_days"
    elif [ "$alert" = budget ]; then
        printf 'ALERT %s %dMB over %dMB\n' "$dir" "$dir_mb" "$budget_mb"
    fi

    if [ "${#big_list[@]}" -gt 0 ]; then
        printf '%s\n' "${big_list[@]}" \
            | sort -rn \
            | awk -F'\t' -v n="$top" -v skip="$skip_big" \
                'NR <= n && $2 != skip { printf "BIG %s %dMB\n", $2, $1 / 1048576 }'
    fi

    if [ "${#old_list[@]}" -gt 0 ]; then
        printf '%s\n' "${old_list[@]}" \
            | sort -rn \
            | awk -F'\t' -v n="$top" -v skip="$skip_old" \
                'NR <= n && $2 != skip { printf "OLD %s %dd\n", $2, $1 }'
    fi

    if [ "$budget_hit" -eq 1 ] && [ "$alert" != budget ]; then
        printf 'BUDGET %s %dMB over %dMB\n' "$dir" "$dir_mb" "$budget_mb"
    fi

    if [ "$alert" = big ]; then
        printf 'ROTATE %s: size %dM, rotate %d, compress\n' "$biggest" "$max_mb" "$max_days"
    elif [ "$alert" = old ]; then
        printf 'ROTATE %s: daily, rotate 14, maxage %d, compress\n' "$oldest" "$max_days"
    fi
done

if [ "$total" -gt 0 ]; then
    exit 1
fi
exit 0
```
