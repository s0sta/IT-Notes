---
id: p653
title: "Secrets in crontabs and env files"
slug: secrets-in-crontabs-and-env-files
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, CyberSecurity, SecretsManagement, DevSecOps]
source: "LinkedIn post P653 · ShellSec series"
linkedin_date: 2030-11-28
design: code
script: cron_secret_scan.sh
---

# Secrets in crontabs and env files

A backup job needs the database password, so someone puts it in `/etc/cron.d/backup`. Six months later it is in a support bundle, a repo mirror and a screenshot. The job never needed it in plain text.

## Quick reference

The full script is at the end of this note: `cron_secret_scan.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash cron_secret_scan.sh /tmp/s0f/cron.d/db
```

**Example output**

```text
/tmp/s0f/cron.d/db:2: DB_PASS=****
FINDING 1 secret-like line
```

## Explained

### What it does

`cron_secret_scan.sh` walks the paths you give it, keeps crontabs and env files, and matches assignment-shaped lines: password, pass, secret, token, api key, access key, private key, credential, authorization. Every hit prints the path, the line and the key, then four stars. The value never reaches stdout.

### What the screen shows

The fourteen lines read each file with awk, lower-case the line for matching, stop at the assignment and print the masked prefix. On the dirty fixture: `/tmp/s0f/cron.d/db`:2: DB_PASS=\*\*\*\* and FINDING 1 secret-like line.

### How to run it

`sudo cron_secret_scan.sh /etc/cron.d /etc/crontab /var/spool/cron /srv/app`, or one .env file. Exit 0 is clean, 1 is a hit, 2 is a missing or unreadable path. It writes nothing.

### The fix

Masking is for the report, not the fix. Rotate the secret first, then move it to a root-only file with mode 0600, or to a secret manager the job can read at runtime. Remove the old value from backups and CI logs if they are reachable.

### Prevention

A pre-commit hook and a CI grep catch the copy in git; the host sweep catches the copy that survives a clean-up.

> **The honest caveat:** the pattern matches names, not entropy, so a variable named APPLE will pass.

> **The lesson:** a secret in a cron file is a secret every process can read.

## In one line

> **A cron line is not a vault.** The host copy survives the repo clean-up.

**Mask, then rotate:** `cron_secret_scan.sh /etc/cron.d`

## Script: cron_secret_scan.sh

Download: [scripts/cron_secret_scan.sh](../scripts/cron_secret_scan.sh)

```bash
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
```
