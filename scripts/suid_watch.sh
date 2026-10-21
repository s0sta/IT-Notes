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
