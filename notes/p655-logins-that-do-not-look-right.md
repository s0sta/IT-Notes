---
id: p655
title: "Logins that do not look right"
slug: logins-that-do-not-look-right
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, CyberSecurity, SecOps, SysAdmin]
source: "LinkedIn post P655 · ShellSec series"
linkedin_date: 2030-12-03
design: code
script: audit_logins.sh
---

# Logins that do not look right

Three failed logins for alice at 09:00, a success at 09:02, and a root session at 02:14. last and lastb hold it all, in a format nobody parses until an incident.

## Quick reference

The full script is at the end of this note: `audit_logins.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash audit_logins.sh /tmp/s0f/last.txt
```

**Example output**

```text
ROOT 02:14 root pts/0 10.0.0.5
FINDING logins: 1
```

## Explained

### What it does

`audit_logins.sh` normalises `last -F -i` and `lastb -F -i` into user, tty, host and a minute. It reports root logins, successes outside 06:00-23:00, users missing from passwd, and three failures then a success for the same user and host inside 30 minutes. Any hit exits 1.

### What the screen shows

The fourteen lines find the month, read the hour, print ROOT and ODD lines and exit 1. On the fixture: ROOT 02:14 root pts/0 10.0.0.5 and FINDING logins: 1. The full script adds the pair and unknown-user passes.

### How to run it

`sudo audit_logins.sh`, or pass a saved last file and `--lastb`. Exit 0 is clean, 1 is a finding, 2 is a missing file or bad option.

### The fix

For root: confirm the ticket, then set PermitRootLogin prohibit-password and give the engineer a named account. For a pair: block the source, force a password reset and review the session. For an unknown user: find the account that should not exist.

### Prevention

Alert on root logins and on failures per source per hour, not a daily count. A brute force that stops at success is invisible in a total.

> **The honest caveat:** last omits the year unless -F is used, and wtmp rotation can hide older sessions.

> **The lesson:** a login is a fact; a pattern of logins is the story.

## In one line

> **Root at 2 a.m. is a question.** The full script adds failed-then-success pairs and unknown users.

**Read both logs**

```bash
last -F -i; sudo lastb -F -i
```

## Script: audit_logins.sh

Download: [scripts/audit_logins.sh](../scripts/audit_logins.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
# audit_logins.sh - find root, odd-hour, paired and unknown logins.
#
# Fixes: three failed logins for alice, a success two minutes later and a root
# session at 02:14, with nobody reading last or lastb. This script normalises
# both files and reports the four patterns that matter.
#
# Usage:
#   sudo ./audit_logins.sh
#   ./audit_logins.sh --last ./last.txt --lastb ./lastb.txt --known ./users.txt
#
# Cron (daily, 06:10):
#   10 6 * * * root /usr/local/sbin/audit_logins.sh >> /var/log/audit_logins.log 2>&1
#
# Exit: 0 clean, 1 login anomaly, 2 usage or unreadable input.
# Reads only. Linux last/lastb from util-linux; -F adds the year, -i shows IPs.
# lastb needs root; without it the pair check is skipped with a NOTE.
# Anomalies: a root login, a success outside --start/--end, at least
# --min-fails failures followed by a success from the same user and host
# within --window minutes on the same day, and a user missing from passwd.
#
# By s0sta.com

IFS=$'\n\t'

LAST_FILE=""
LASTB_FILE=""
KNOWN_FILE=""
WINDOW=30
MIN_FAILS=3
START_HOUR=6
END_HOUR=23

usage() {
  cat <<'EOF'
Usage: audit_logins.sh [options] [LAST_FILE]

Report root, odd-hour, failed-then-success and unknown-user logins.

Options:
  --last FILE       read saved last output instead of running last -F -i
  --lastb FILE      read saved lastb output instead of running lastb -F -i
  --known FILE      known users, one per line (default: passwd database)
  --window N        failed-then-success window in minutes (default: 30)
  --min-fails N     failures needed before a success counts (default: 3)
  --start H         first normal hour, 0-23 (default: 6)
  --end H           last normal hour, 0-23 (default: 23)
  -h, --help        show this help and exit

LAST_FILE is a saved last output, shorthand for --last FILE.
Exit: 0 clean, 1 login anomaly, 2 usage or unreadable input.
By s0sta.com
EOF
}

die() {
  printf 'ERROR %s\n' "$1" >&2
  exit 2
}

is_int() {
  case $1 in
    ''|*[!0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

while [ "$#" -gt 0 ]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    --last)
      [ "$#" -ge 2 ] || die "$1 needs a file"
      LAST_FILE=$2
      shift 2
      ;;
    --lastb)
      [ "$#" -ge 2 ] || die "$1 needs a file"
      LASTB_FILE=$2
      shift 2
      ;;
    --known)
      [ "$#" -ge 2 ] || die "$1 needs a file"
      KNOWN_FILE=$2
      shift 2
      ;;
    --window)
      [ "$#" -ge 2 ] || die "$1 needs a number"
      WINDOW=$2
      shift 2
      ;;
    --min-fails)
      [ "$#" -ge 2 ] || die "$1 needs a number"
      MIN_FAILS=$2
      shift 2
      ;;
    --start)
      [ "$#" -ge 2 ] || die "$1 needs an hour"
      START_HOUR=$2
      shift 2
      ;;
    --end)
      [ "$#" -ge 2 ] || die "$1 needs an hour"
      END_HOUR=$2
      shift 2
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      [ -z "$LAST_FILE" ] || die "unexpected argument: $1"
      LAST_FILE=$1
      shift
      ;;
  esac
done

is_int "$WINDOW" && [ "$WINDOW" -ge 1 ] && [ "$WINDOW" -le 1440 ] \
  || die "--window needs a number from 1 to 1440"
is_int "$MIN_FAILS" && [ "$MIN_FAILS" -ge 1 ] && [ "$MIN_FAILS" -le 1000 ] \
  || die "--min-fails needs a number from 1 to 1000"
is_int "$START_HOUR" && [ "$START_HOUR" -ge 0 ] && [ "$START_HOUR" -le 23 ] \
  || die "--start needs an hour from 0 to 23"
is_int "$END_HOUR" && [ "$END_HOUR" -ge 0 ] && [ "$END_HOUR" -le 23 ] \
  || die "--end needs an hour from 0 to 23"
[ "$START_HOUR" -lt "$END_HOUR" ] || die "--start must be before --end"

WORK=$(mktemp -d "${TMPDIR:-/tmp}/audit_logins.XXXXXX") || die "cannot create a work directory"
trap 'rm -rf "$WORK"' EXIT

if [ -n "$LAST_FILE" ]; then
  [ -r "$LAST_FILE" ] || die "cannot read --last file: $LAST_FILE"
  last_src=$LAST_FILE
else
  command -v last >/dev/null 2>&1 || die "last not found: pass --last FILE"
  if ! LC_ALL=C last -F -i > "$WORK/last" 2>/dev/null; then
    die "last -F -i failed: pass --last FILE"
  fi
  last_src=$WORK/last
fi

if [ -n "$LASTB_FILE" ]; then
  [ -r "$LASTB_FILE" ] || die "cannot read --lastb file: $LASTB_FILE"
  lastb_src=$LASTB_FILE
else
  : > "$WORK/lastb"
  lastb_src=$WORK/lastb
  if command -v lastb >/dev/null 2>&1; then
    if ! LC_ALL=C lastb -F -i > "$WORK/lastb" 2>/dev/null; then
      : > "$WORK/lastb"
      printf 'NOTE lastb unreadable: failed-login pairs skipped\n' >&2
    fi
  else
    printf 'NOTE lastb not installed: failed-login pairs skipped\n' >&2
  fi
fi

if [ -n "$KNOWN_FILE" ]; then
  [ -r "$KNOWN_FILE" ] || die "cannot read --known file: $KNOWN_FILE"
  awk '{ print $1 }' "$KNOWN_FILE" > "$WORK/known"
else
  : > "$WORK/known"
  if command -v getent >/dev/null 2>&1; then
    getent passwd 2>/dev/null | cut -d: -f1 > "$WORK/known" || true
  fi
  if [ ! -s "$WORK/known" ]; then
    cut -d: -f1 /etc/passwd > "$WORK/known" 2>/dev/null || true
  fi
fi

normalize() {
  awk -v default_year="$(date +%Y)" '
    BEGIN { split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec", mon, " ") }
    $1 == "reboot" || $1 == "shutdown" || $1 == "wtmp" { next }
    {
      mi = 0
      for (i = 2; i <= NF; i++) {
        for (k = 1; k <= 12; k++) {
          if ($i == mon[k]) { mi = i; mo = k; break }
        }
        if (mi > 0) break
      }
      if (mi == 0) next
      day = $(mi + 1)
      tim = $(mi + 2)
      yr = $(mi + 3)
      if (day !~ /^[0-9]+$/) next
      if (tim !~ /^[0-9][0-9]:[0-9][0-9](:[0-9][0-9])?$/) next
      if (yr !~ /^[0-9][0-9][0-9][0-9]$/) yr = default_year
      split(tim, t, ":")
      host = (mi >= 5) ? $3 : "-"
      printf "%s %s %s %s %d %d %d %d\n", $1, $2, host, yr, mo, day, t[1], t[2]
    }
  ' "$1"
}

{
  normalize "$last_src" | sed 's/^/L /'
  normalize "$lastb_src" | sed 's/^/B /'
} > "$WORK/records"

status=0
awk -v window="$WINDOW" -v minfails="$MIN_FAILS" \
    -v starth="$START_HOUR" -v endh="$END_HOUR" '
  FNR == NR { known[$1] = 1; next }
  {
    src = $1; user = $2; tty = $3; host = $4
    yr = $5; mo = $6 + 0; day = $7 + 0; hh = $8 + 0; mm = $9 + 0
    key = user SUBSEP host SUBSEP yr SUBSEP mo SUBSEP day
    tod = hh * 60 + mm
    if (!(user in known)) {
      unk[++nu] = sprintf("UNKNOWN %02d:%02d %s %s %s", hh, mm, user, tty, host)
    }
    if (src == "L") {
      if (user == "root") {
        root[++nr] = sprintf("ROOT %02d:%02d %s %s %s", hh, mm, user, tty, host)
      } else if (tod < starth * 60 || tod > endh * 60) {
        odd[++no] = sprintf("ODD %02d:%02d %s %s %s", hh, mm, user, tty, host)
      }
      ns++
      s_key[ns] = key
      s_tod[ns] = tod
      s_hm[ns] = sprintf("%02d:%02d", hh, mm)
      s_user[ns] = user
      s_host[ns] = host
    } else {
      nf = ++failn[key]
      fail[key, nf] = tod
    }
  }
  END {
    for (i = 1; i <= ns; i++) {
      c = 0
      k = s_key[i]
      for (j = 1; j <= failn[k]; j++) {
        t = fail[k, j]
        if (t <= s_tod[i] && s_tod[i] - t <= window) c++
      }
      if (c >= minfails) {
        pair[++np] = sprintf("PAIR %s %s %d fails then success %s",
                             s_hm[i], s_user[i], c, s_host[i])
      }
    }
    total = nr + no + np + nu
    if (total == 0) {
      print "OK no login anomalies"
      exit 0
    }
    printf "FINDING %d login anomalies\n", total
    for (i = 1; i <= nr; i++) print root[i]
    for (i = 1; i <= no; i++) print odd[i]
    for (i = 1; i <= np; i++) print pair[i]
    for (i = 1; i <= nu; i++) print unk[i]
    exit 1
  }
' "$WORK/known" "$WORK/records" || status=$?
exit "$status"
```
