#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# backup_sync.sh - verify a mirror before and after rsync copies it.
#
# Fixes: a nightly backup that exits 0 and copies nothing. The job proves
# rsync ran, not that the target matches the source, so a wrong path or an
# unmounted volume stays invisible until the day someone restores.
#
# The default is a dry run: it measures both trees, runs rsync with
# --dry-run, and reports the drift. --apply performs the copy and then
# measures again. --delete makes the target a mirror (use with care).
#
# Usage:
#   backup_sync.sh --source /srv/config --target /backup/config
#   backup_sync.sh --source /srv/config --target /backup/config --apply
#   backup_sync.sh --source /srv/config --target /backup/config --apply --delete
#
# Cron (one run measures, copies and verifies again at 02:30):
#   30 2 * * * /usr/local/bin/backup_sync.sh --source /srv/config \
#     --target /backup/config --min-files 10 --apply >> /var/log/backup.log 2>&1
#
# Exit codes:
#   0  target matches source (dry run) or the copy verified (apply)
#   1  drift, source below --min-files, or the copy did not verify
#   2  usage error, unreadable tree, or rsync missing
#
# Requires rsync, GNU find (find -printf) and numfmt (coreutils). The target
# must already exist, so a dry run never creates a directory. Tested on clean
# and dirty fixture trees in /tmp; services are not touched.
# By s0sta.com

PROG=${0##*/}
src=""
dst=""
min_files=1
apply=0
delete=0
dry_out=""

usage() {
  cat <<'EOF'
backup_sync.sh - verify a mirror before and after rsync copies it

Usage:
  backup_sync.sh --source DIR --target DIR [options]

Options:
  --source DIR      directory to copy from (read only)
  --target DIR      directory to copy to (must exist)
  --min-files N     fail if the source has fewer than N files; default 1
  --delete          delete target files missing from the source (mirror)
  --apply           run rsync; without it the dry run only reports drift
  -h, --help        show this help and exit 0

Examples:
  backup_sync.sh --source /srv/config --target /backup/config
  backup_sync.sh --source /srv/config --target /backup/config --apply
  backup_sync.sh --source /srv/config --target /backup/config --apply --delete

Exit: 0 in sync, 1 drift or failed copy, 2 usage or unreadable input.
EOF
}

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 2
}

# shellcheck disable=SC2329  # called by the EXIT trap
cleanup() {
  if [[ -n $dry_out ]]; then
    rm -f -- "$dry_out"
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

n_files() {
  if (($1 == 1)); then
    printf '1 file'
  else
    printf '%d files' "$1"
  fi
}

measure() {
  local dir=$1 n b
  n=$(find "$dir" -xdev -type f -printf '.' | wc -c) || return 1
  n=${n// /}
  b=$(find "$dir" -xdev -type f -printf '%s\n' |
    awk '{ total += $1 } END { printf "%.0f", total + 0 }') || return 1
  printf '%s %s\n' "$n" "$b"
}

while (($#)); do
  case $1 in
    --source)
      [[ $# -ge 2 ]] || die "--source needs a directory"
      src=$2
      shift 2
      ;;
    --target)
      [[ $# -ge 2 ]] || die "--target needs a directory"
      dst=$2
      shift 2
      ;;
    --min-files)
      [[ $# -ge 2 ]] || die "--min-files needs a number"
      min_files=$2
      shift 2
      ;;
    --apply)
      apply=1
      shift
      ;;
    --delete)
      delete=1
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

[[ -n $src ]] || die "--source is required (try --help)"
[[ -n $dst ]] || die "--target is required (try --help)"
[[ $min_files =~ ^[0-9]+$ ]] || die "--min-files must be a whole number"
[[ -d $src ]] || die "source is not a directory: $src"
[[ -d $dst ]] || die "target is not a directory: $dst"
[[ -r $src ]] || die "cannot read source: $src"
[[ -r $dst ]] || die "cannot read target: $dst"
command -v rsync >/dev/null 2>&1 || die "rsync is not installed"
command -v find >/dev/null 2>&1 || die "find is not installed"
command -v numfmt >/dev/null 2>&1 || die "numfmt is not installed (coreutils)"

if [[ $src -ef $dst ]]; then
  die "source and target are the same directory"
fi

src_info=$(measure "$src") || die "cannot measure source: $src"
src_files=${src_info%% *}
src_bytes=${src_info#* }
dst_info=$(measure "$dst") || die "cannot measure target: $dst"
dst_files=${dst_info%% *}
dst_bytes=${dst_info#* }

printf 'MODE %s\n' "$([[ $apply -eq 1 ]] && printf apply || printf dry-run)"
printf 'SOURCE %s: %d files, %s\n' "$src" "$src_files" "$(fmt_bytes "$src_bytes")"
printf 'TARGET %s: %d files, %s\n' "$dst" "$dst_files" "$(fmt_bytes "$dst_bytes")"

if ((src_files < min_files)); then
  printf 'FAIL source has %s, below --min-files %d\n' \
    "$(n_files "$src_files")" "$min_files"
  printf 'FAIL refusing to call an empty source a good backup\n'
  exit 1
fi

dry_out=$(mktemp "${TMPDIR:-/tmp}/backup_sync.XXXXXX") || die "mktemp failed"

rargs=(-a --itemize-changes --stats)
if ((delete == 1)); then
  rargs+=(--delete)
fi

if ! rsync "${rargs[@]}" --dry-run -- "$src"/ "$dst"/ >"$dry_out" 2>&1; then
  printf 'FAIL rsync dry run failed\n'
  tail -n 5 "$dry_out" >&2
  exit 1
fi

transferred=$(awk -F': *' '/Number of (regular )?files transferred/ {
  value = $2; gsub(/,/, "", value); print value
}' "$dry_out" | tail -n 1)
if [[ ! $transferred =~ ^[0-9]+$ ]]; then
  transferred=0
fi

xfer_bytes=$(awk -F': *' '/Total transferred file size/ {
  value = $2; sub(/ .*/, "", value); gsub(/,/, "", value); print value
}' "$dry_out" | tail -n 1)
if [[ ! $xfer_bytes =~ ^[0-9]+$ ]]; then
  xfer_bytes=0
fi

plan_files=$transferred
if ((plan_files == 0)); then
  plan_files=$((src_files - dst_files))
  if ((plan_files < 0)); then
    plan_files=0
  fi
fi
plan_bytes=$((src_bytes - dst_bytes))
if ((plan_bytes < 0)); then
  plan_bytes=0
fi
if ((plan_bytes == 0 && xfer_bytes > 0)); then
  plan_bytes=$xfer_bytes
fi

if ((src_files == dst_files && src_bytes == dst_bytes && transferred == 0)); then
  printf 'DRIFT none: target matches source\n'
  printf 'OK %d files, %s in sync\n' "$src_files" "$(fmt_bytes "$src_bytes")"
  exit 0
fi

printf 'DRIFT target %d/%d files, %s/%s\n' \
  "$dst_files" "$src_files" "$(fmt_bytes "$dst_bytes")" "$(fmt_bytes "$src_bytes")"
printf 'PLAN rsync %s, %s\n' "$(n_files "$plan_files")" "$(fmt_bytes "$plan_bytes")"
if ((dst_files > src_files)); then
  printf 'EXTRA target holds %s missing from source\n' \
    "$(n_files "$((dst_files - src_files))")"
  if ((delete == 0)); then
    printf 'NOTE rerun with --delete to mirror, or leave the extra files\n'
  fi
fi

if ((apply == 0)); then
  printf 'DRY-RUN nothing copied. Add --apply to sync.\n'
  exit 1
fi

start=$(date +%s)
if ! rsync "${rargs[@]}" -- "$src"/ "$dst"/ >"$dry_out" 2>&1; then
  printf 'FAIL rsync copy failed\n'
  tail -n 5 "$dry_out" >&2
  exit 1
fi
elapsed=$(( $(date +%s) - start ))

dst_info=$(measure "$dst") || die "cannot measure target after copy: $dst"
dst_files=${dst_info%% *}
dst_bytes=${dst_info#* }

printf 'SYNCED %s in %ds\n' "$(n_files "$plan_files")" "$elapsed"
if ((src_files == dst_files && src_bytes == dst_bytes)); then
  printf 'VERIFY target matches source: %s, %s\n' \
    "$(n_files "$dst_files")" "$(fmt_bytes "$dst_bytes")"
  exit 0
fi
printf 'FAIL target still differs: %d/%d files, %s/%s\n' \
  "$dst_files" "$src_files" "$(fmt_bytes "$dst_bytes")" "$(fmt_bytes "$src_bytes")"
exit 1
