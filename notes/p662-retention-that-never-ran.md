---
id: p662
title: "Retention that never ran"
slug: retention-that-never-ran
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, SysAdmin, Automation, Storage]
source: "LinkedIn post P662 · ShellSec series"
linkedin_date: 2030-12-19
design: code
script: retention_cleanup.sh
---

# Retention that never ran

A retention policy says thirty days. The volume fills, because the policy is a paragraph in a wiki and the deletion was a ticket someone closed in 2024.

## Quick reference

The full script is at the end of this note: `retention_cleanup.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
retention_cleanup.sh --path /var/log/app --days 30
```

**Example output**

```text
MATCH 3 files, 13.8MB reclaimable
RM app-2026-07.log 80d 12.0MB
```

## Explained

### What it does

`retention_cleanup.sh` scans one path, keeps regular files older than `--days`, and prints the oldest ten with their age and size, then the total reclaimable. The default is a dry run. `--apply` deletes, and `--max-delete` refuses a plan larger than 10,000 files.

### What the screen shows

The fourteen lines read the path and the age, collect matching files with find, sort them oldest first, and sum the bytes. On the fixture they print MATCH 3 files, 13.8MB reclaimable, then RM `app-2026-07.log 80d 12.0MB`.

### How to run it

`retention_cleanup.sh --path /var/log/app --days 30`, then the same line with `--apply`. Exit 0 means nothing matched, 1 means a plan or a failed deletion, 2 means bad input. The cron line in the header runs the dry run on Monday and the apply at 03:15.

### The fix

Read the plan before the apply. The oldest file names the producer: a logrotate rule that stopped matching, an application that writes its own dated files, a backup that never expires. Fix the producer, then let the job delete.

### Prevention

Alert when the reclaimable total grows for three nights. A retention job that suddenly has more to delete is a producer that changed, not a disk that grew.

> **The honest caveat:** the scan stays on one filesystem, so a volume mounted under the path is invisible.

> **The lesson:** a retention policy is not a cron job until it runs.

## In one line

> **Retention is a verb.** A policy with no job behind it is a hope with a date.

**Plan before delete:** `retention_cleanup.sh --path /var`

## Script: retention_cleanup.sh

Download: [scripts/retention_cleanup.sh](../scripts/retention_cleanup.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# retention_cleanup.sh - plan and apply age-based file retention.
#
# Fixes: a retention rule that lives in a wiki and never ran, so the volume
# fills one old log at a time until a write fails at 03:00.
#
# The default is a dry run: it prints every file it would delete, the oldest
# first, and the total reclaimable. Nothing is removed until --apply.
#
# Usage:
#   retention_cleanup.sh --path /var/log/app --days 30
#   retention_cleanup.sh --path /var/log/app --days 30 --apply
#   retention_cleanup.sh --path /var/log/app --days 30 --pattern '*.log'
#
# Cron (report every Monday at 06:00, apply every night at 03:15):
#   0 6 * * 1 /usr/local/bin/retention_cleanup.sh --path /var/log/app \
#     --days 30 >> /var/log/retention.log 2>&1
#   15 3 * * * /usr/local/bin/retention_cleanup.sh --path /var/log/app \
#     --days 30 --apply >> /var/log/retention.log 2>&1
#
# Exit codes:
#   0  nothing matched (dry run) or every planned file was deleted (apply)
#   1  files matched (dry run) or at least one deletion failed (apply)
#   2  usage error, unreadable path, or a failed scan
#
# Requires GNU find (find -printf), GNU sort (sort -z) and numfmt
# (coreutils). Tested on a fixture tree in /tmp: clean exit 0, dirty exit 1,
# missing args exit 2.
# By s0sta.com

PROG=${0##*/}
path=""
days=30
pattern="*"
max_delete=10000
apply=0
tmp=""

usage() {
  cat <<'EOF'
retention_cleanup.sh - plan and apply age-based file retention

Usage:
  retention_cleanup.sh --path DIR --days N [options]

Options:
  --path DIR        directory to scan (required, not / and not a symlink)
  --days N          age in whole days; default 30
  --pattern GLOB    only files whose name matches GLOB; default '*'
  --max-delete N    refuse to apply more than N deletions; default 10000
  --apply           delete the files; without it nothing is removed
  -h, --help        show this help and exit 0

Examples:
  retention_cleanup.sh --path /var/log/app --days 30
  retention_cleanup.sh --path /var/log/app --days 30 --pattern '*.log'
  retention_cleanup.sh --path /var/log/app --days 30 --apply

Exit: 0 nothing to do, 1 files matched or a deletion failed, 2 usage.
EOF
}

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 2
}

# shellcheck disable=SC2329  # called by the EXIT trap
cleanup() {
  if [[ -n $tmp ]]; then
    rm -f -- "$tmp"
  fi
}
trap cleanup EXIT

fmt_bytes() {
  if (($1 == 0)); then
    printf '0B'
    return
  fi
  numfmt --to=iec --suffix=B --format='%.1f' -- "$1"
}

while (($#)); do
  case $1 in
    --path)
      [[ $# -ge 2 ]] || die "--path needs a directory"
      path=$2
      shift 2
      ;;
    --days)
      [[ $# -ge 2 ]] || die "--days needs a number"
      days=$2
      shift 2
      ;;
    --pattern)
      [[ $# -ge 2 ]] || die "--pattern needs a glob"
      pattern=$2
      shift 2
      ;;
    --max-delete)
      [[ $# -ge 2 ]] || die "--max-delete needs a number"
      max_delete=$2
      shift 2
      ;;
    --apply)
      apply=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      die "unknown option: $1 (try --help)"
      ;;
    *)
      die "unexpected argument: $1 (try --help)"
      ;;
  esac
done

[[ -n $path ]] || die "--path is required (try --help)"
[[ $days =~ ^[0-9]+$ ]] || die "--days must be a whole number"
((days >= 1)) || die "--days must be at least 1"
[[ $max_delete =~ ^[0-9]+$ ]] || die "--max-delete must be a whole number"
((max_delete >= 1)) || die "--max-delete must be at least 1"
[[ -d $path ]] || die "not a directory: $path"
if [[ -L $path ]]; then
  die "refusing a symlink path: $path"
fi
while [[ $path == */ && $path != "/" ]]; do
  path=${path%/}
done
[[ -n $path ]] || die "refusing to scan /"
[[ -r $path ]] || die "cannot read: $path"
command -v find >/dev/null 2>&1 || die "find is not installed"
command -v sort >/dev/null 2>&1 || die "sort is not installed"
command -v numfmt >/dev/null 2>&1 || die "numfmt is not installed (coreutils)"

tmp=$(mktemp "${TMPDIR:-/tmp}/retention.XXXXXX") || die "mktemp failed"
if ! find "$path" -xdev -type f -mtime +"$days" -name "$pattern" \
      -printf '%T@ %s %p\0' | sort -z -n >"$tmp"; then
  die "scan failed under: $path"
fi

now=$(date +%s)
total=0
count=0
while IFS= read -r -d '' rec; do
  rest=${rec#* }
  size=${rest%% *}
  count=$((count + 1))
  total=$((total + size))
done <"$tmp"

printf 'MODE %s\n' "$([[ $apply -eq 1 ]] && printf apply || printf dry-run)"
printf 'PATH %s\n' "$path"
printf 'OLDER %d days\n' "$days"
printf 'MATCH %d files, %s reclaimable\n' "$count" "$(fmt_bytes "$total")"

if ((count == 0)); then
  printf 'OK nothing older than %d days under %s\n' "$days" "$path"
  exit 0
fi

shown=0
while IFS= read -r -d '' rec; do
  if ((shown >= 10)); then
    break
  fi
  stamp=${rec%% *}
  rest=${rec#* }
  size=${rest%% *}
  file=${rest#* }
  age=$(((now - ${stamp%%.*}) / 86400))
  rel=${file#"$path"/}
  printf 'RM %s %dd %s\n' "$rel" "$age" "$(fmt_bytes "$size")"
  shown=$((shown + 1))
done <"$tmp"

if ((count > shown)); then
  printf 'MORE %d files not listed\n' "$((count - shown))"
fi

if ((apply == 0)); then
  printf 'DRY-RUN nothing deleted. Add --apply to delete.\n'
  exit 1
fi

if ((count > max_delete)); then
  printf 'REFUSE %d files exceeds --max-delete %d; nothing deleted\n' \
    "$count" "$max_delete"
  exit 1
fi

removed=0
failed=0
freed=0
while IFS= read -r -d '' rec; do
  rest=${rec#* }
  size=${rest%% *}
  file=${rest#* }
  if rm -f -- "$file"; then
    removed=$((removed + 1))
    freed=$((freed + size))
  else
    failed=$((failed + 1))
    printf 'FAIL could not delete %s\n' "$file" >&2
  fi
done <"$tmp"

printf 'DELETED %d files, %s freed\n' "$removed" "$(fmt_bytes "$freed")"
if ((failed > 0)); then
  printf 'FAIL %d deletions failed\n' "$failed"
  exit 1
fi
exit 0
```
