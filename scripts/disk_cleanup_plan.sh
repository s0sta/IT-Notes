#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# disk_cleanup_plan.sh - rank what owns the disk, with a risk note per item.
#
# Fixes: the disk nobody will clean. Every candidate looks dangerous, so the
# cleanup never happens, and the volume fills one directory at a time until a
# write fails. This tool never deletes. It ranks the biggest directories and
# the oldest large files, and prints what each one is and how to treat it.
#
# Usage:
#   disk_cleanup_plan.sh --path /var
#   disk_cleanup_plan.sh --path /var --top 15 --min-size 500M --older-than 60
#
# Cron (weekly report, Monday 06:00):
#   0 6 * * 1 /usr/local/bin/disk_cleanup_plan.sh --path /var \
#     >> /var/log/disk_cleanup_plan.log 2>&1
#
# Exit codes:
#   0  nothing above the size and age filters
#   1  at least one directory or file is worth reviewing
#   2  usage error or unreadable path
#
# Requires GNU du (du -0 -B1 -d), GNU find (-printf), GNU sort (-z),
# GNU head (-z) and numfmt (coreutils). Read-only: it never deletes,
# truncates or moves anything. Tested on clean and dirty fixture trees in
# /tmp; no service is touched.
# By s0sta.com

PROG=${0##*/}
path="/var"
top=10
min_raw="100M"
min_bytes=0
older=30
tmp_dirs=""
tmp_files=""
tmp_err=""

usage() {
  cat <<'EOF'
disk_cleanup_plan.sh - rank what owns the disk, with a risk note per item

Usage:
  disk_cleanup_plan.sh [options]

Options:
  --path DIR        directory to scan; default /var
  --top N           rows per list; default 10
  --min-size SIZE   directory or file size floor, K/M/G/T; default 100M
  --older-than N    file age floor in days; default 30
  -h, --help        show this help and exit 0

Examples:
  disk_cleanup_plan.sh --path /var
  disk_cleanup_plan.sh --path /srv --min-size 1G --older-than 90 --top 20

Read-only: the plan is printed, nothing is deleted.
Exit: 0 nothing to review, 1 plan items found, 2 usage or unreadable path.
EOF
}

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 2
}

# shellcheck disable=SC2329  # called by the EXIT trap
cleanup() {
  local f
  for f in "$tmp_dirs" "$tmp_files" "$tmp_err"; do
    if [[ -n $f ]]; then
      rm -f -- "$f"
    fi
  done
}
trap cleanup EXIT

fmt_bytes() {
  if (($1 == 0)); then
    printf '0B'
    return
  fi
  numfmt --to=iec --suffix=B --format='%.1f' -- "$1"
}

to_bytes() {
  local raw=$1 suffix mult=1 number
  suffix=${raw: -1}
  case $suffix in
    k|K) mult=1024 ; raw=${raw%?} ;;
    m|M) mult=$((1024 * 1024)) ; raw=${raw%?} ;;
    g|G) mult=$((1024 * 1024 * 1024)) ; raw=${raw%?} ;;
    t|T) mult=$((1024 * 1024 * 1024 * 1024)) ; raw=${raw%?} ;;
  esac
  number=$raw
  [[ $number =~ ^[0-9]+$ ]] || return 1
  printf '%d' $((number * mult))
}

risk_note() {
  case $1 in
    */log|*/log/*)
      printf 'logs: rotate or vacuum, never rm the live file'
      ;;
    *docker*|*containerd*)
      printf 'images in use: prune, never rm -rf'
      ;;
    *mysql*|*postgres*|*pgsql*)
      printf 'database files: back up, never delete by hand'
      ;;
    */cache|*/cache/*)
      printf 'cache: safe to clear, services refill it'
      ;;
    */home/*|*/srv/*)
      printf 'owner data: confirm with the owner first'
      ;;
    *)
      printf 'unclassified: inspect before touching'
      ;;
  esac
}

while (($#)); do
  case $1 in
    --path)
      [[ $# -ge 2 ]] || die "--path needs a directory"
      path=$2
      shift 2
      ;;
    --top)
      [[ $# -ge 2 ]] || die "--top needs a number"
      top=$2
      shift 2
      ;;
    --min-size)
      [[ $# -ge 2 ]] || die "--min-size needs a size"
      min_raw=$2
      shift 2
      ;;
    --older-than)
      [[ $# -ge 2 ]] || die "--older-than needs a number of days"
      older=$2
      shift 2
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

[[ $top =~ ^[0-9]+$ ]] || die "--top must be a whole number"
((top >= 1)) || die "--top must be at least 1"
[[ $older =~ ^[0-9]+$ ]] || die "--older-than must be a whole number"
((older >= 1)) || die "--older-than must be at least 1"
min_bytes=$(to_bytes "$min_raw") ||
  die "--min-size must look like 500M, 2G or a byte count"
((min_bytes >= 1)) || die "--min-size must be at least 1 byte"
[[ -d $path ]] || die "not a directory: $path"
if [[ -L $path ]]; then
  die "refusing a symlink path: $path"
fi
while [[ $path == */ && $path != "/" ]]; do
  path=${path%/}
done
[[ -n $path ]] || die "refusing to scan /"
[[ -r $path ]] || die "cannot read: $path"

command -v du >/dev/null 2>&1 || die "du is not installed"
command -v find >/dev/null 2>&1 || die "find is not installed"
command -v numfmt >/dev/null 2>&1 || die "numfmt is not installed (coreutils)"

tmp_dirs=$(mktemp "${TMPDIR:-/tmp}/disk_plan_dirs.XXXXXX") || die "mktemp failed"
tmp_files=$(mktemp "${TMPDIR:-/tmp}/disk_plan_files.XXXXXX") || die "mktemp failed"
tmp_err=$(mktemp "${TMPDIR:-/tmp}/disk_plan_err.XXXXXX") || die "mktemp failed"

printf 'PATH %s\n' "$path"
printf 'FILTER size %s, age %sd\n' "$min_raw" "$older"

du -0 -x -B1 -d 1 "$path" 2>"$tmp_err" |
  sort -z -rn | head -z -n "$((top + 1))" >"$tmp_dirs" || true
errs=$(wc -l <"$tmp_err" | tr -d ' ')
if ((errs > 0)); then
  printf 'NOTE %d paths unreadable during the directory scan\n' "$errs"
fi

dir_count=0
while IFS= read -r -d '' rec; do
  size=${rec%%$'\t'*}
  dir=${rec#*$'\t'}
  if [[ $dir == "$path" ]]; then
    continue
  fi
  if ((size < min_bytes)); then
    continue
  fi
  printf 'DIR %s %s\n' "$(fmt_bytes "$size")" "$dir"
  printf '  RISK %s\n' "$(risk_note "$dir")"
  dir_count=$((dir_count + 1))
  if ((dir_count >= top)); then
    break
  fi
done <"$tmp_dirs"

: >"$tmp_err"
find "$path" -xdev -type f -size +"$min_bytes"c -mtime +"$older" \
  -printf '%T@ %s %p\0' 2>"$tmp_err" |
  sort -z -n | head -z -n "$top" >"$tmp_files" || true
errs=$(wc -l <"$tmp_err" | tr -d ' ')
if ((errs > 0)); then
  printf 'NOTE %d paths unreadable during the file scan\n' "$errs"
fi

now=$(date +%s)
file_count=0
while IFS= read -r -d '' rec; do
  stamp=${rec%% *}
  rest=${rec#* }
  size=${rest%% *}
  file=${rest#* }
  age=$(((now - ${stamp%%.*}) / 86400))
  printf 'FILE %s %dd %s\n' "$(fmt_bytes "$size")" "$age" "$file"
  printf '  RISK %s\n' "$(risk_note "$file")"
  file_count=$((file_count + 1))
done <"$tmp_files"

dir_word="directories"
if ((dir_count == 1)); then
  dir_word="directory"
fi
file_word="files"
if ((file_count == 1)); then
  file_word="file"
fi

printf 'PLAN %d %s, %d %s to review\n' \
  "$dir_count" "$dir_word" "$file_count" "$file_word"
printf 'READ-ONLY nothing was deleted.\n'

if ((dir_count == 0 && file_count == 0)); then
  printf 'OK nothing over the filter under %s\n' "$path"
  exit 0
fi
exit 1
