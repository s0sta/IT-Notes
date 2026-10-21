#!/usr/bin/env bash
set -euo pipefail
# cron_secret_scan.sh - find secret-like assignments in crontabs and env files.
#
# Fixes: a database password or API token pasted into /etc/cron.d or a .env
# file, where the service account, a backup and a support bundle can all read
# it. The scan prints the path, the line, the key and four stars. The value is
# never written to stdout.
#
# Usage:
#   sudo ./cron_secret_scan.sh /etc/cron.d /etc/crontab /var/spool/cron /srv/app
#   ./cron_secret_scan.sh /srv/app/.env
#
# Cron (daily, 05:30):
#   30 5 * * * root /usr/local/sbin/cron_secret_scan.sh /etc /srv >> /var/log/cron_secret.log 2>&1
#
# Exit: 0 clean, 1 secret-like line found, 2 usage or unreadable path.
# A path that names a file is always scanned. A directory is walked with GNU
# find and only crontabs and env files are read (text files under 1 MB).
# Matching is by key name, not by entropy, so it is deliberately noisy.
#
# By s0sta.com

IFS=$'\n\t'

DEFAULT_PATHS=(
  /etc/cron.d
  /etc/crontab
  /etc/cron.daily
  /etc/cron.hourly
  /etc/cron.weekly
  /etc/cron.monthly
  /var/spool/cron
  /etc/environment
)

PATHS=()
FILES=()

usage() {
  cat <<'EOF'
Usage: cron_secret_scan.sh [options] [PATH...]

Scan crontabs and env files for secret-like assignments and mask the value.

Options:
  -h, --help   show this help and exit

With no PATH, the usual cron locations and /etc/environment are scanned.
A PATH that is a file is scanned as given; a directory is filtered to
crontabs and env files.

Exit: 0 clean, 1 secret-like line found, 2 usage or unreadable path.
By s0sta.com
EOF
}

die() {
  printf 'ERROR %s\n' "$1" >&2
  exit 2
}

is_target() {
  local path=$1 base
  base=${path##*/}
  case $base in
    .env|.env.*|*.env|env|environment|crontab) return 0 ;;
  esac
  case $path in
    */cron.d/*|*/cron.daily/*|*/cron.hourly/*|*/cron.weekly/*|*/cron.monthly/*|*/spool/cron/*) return 0 ;;
  esac
  return 1
}

collect() {
  local p f
  for p in "$@"; do
    if [ -f "$p" ]; then
      printf '%s\n' "$p"
    elif [ -d "$p" ]; then
      while IFS= read -r f; do
        if is_target "$f"; then
          printf '%s\n' "$f"
        fi
      done < <(find "$p" -xdev -type f -size -1024k 2>/dev/null)
    fi
  done
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
  for p in "${DEFAULT_PATHS[@]}"; do
    if [ -e "$p" ]; then
      PATHS+=("$p")
    fi
  done
else
  for p in "${PATHS[@]}"; do
    [ -e "$p" ] || die "missing path: $p"
    [ -r "$p" ] || die "unreadable path: $p"
  done
fi

if [ "${#PATHS[@]}" -eq 0 ]; then
  printf 'SKIP no cron or env paths found\n'
  exit 0
fi

while IFS= read -r f; do
  FILES+=("$f")
done < <(collect "${PATHS[@]}")

nfiles=${#FILES[@]}
if [ "$nfiles" -eq 0 ]; then
  printf 'SKIP no cron or env files under %d paths\n' "${#PATHS[@]}"
  exit 0
fi

status=0
awk -v files="$nfiles" '
  {
    low = tolower($0)
    if (match(low, /(^|[^a-z])(password|passwd|pass|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential|authorization)[a-z0-9_-]*[ \t]*[=:]/)) {
      printf "%s:%d: %s****\n", FILENAME, FNR, substr($0, 1, RSTART + RLENGTH - 1)
      n++
    }
  }
  END {
    if (n > 0) {
      printf "FINDING %d secret-like %s\n", n, (n == 1 ? "line" : "lines")
    } else {
      printf "OK no secret-like lines in %d files\n", files
    }
    exit (n > 0)
  }
' "${FILES[@]}" || status=$?
exit "$status"
