---
id: p664
title: "The cron job that overlapped"
slug: the-cron-job-that-overlapped
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Cron, Linux, SRE, Automation]
source: "LinkedIn post P664 · ShellSec series"
linkedin_date: 2030-12-24
design: code
script: cron_wrapper.sh
---

# The cron job that overlapped

The job takes twelve minutes and the cron line starts it every five. At 03:05 the second run opens the same output directory while the first is writing, and both exit 0 with half a ledger.

## Quick reference

The full script is at the end of this note: `cron_wrapper.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
cron_wrapper.sh -- backup & cron_wrapper.sh -- backup
```

**Example output**

```text
SKIP backup: lock held, exit 75
LOCK backup.lock
```

## Explained

### What it does

`cron_wrapper.sh` takes an exclusive flock before the command starts. A run that cannot get the lock prints the skip and exits 75 without touching data. Inside the lock it stamps a log, runs the command under timeout, and calls `--alert` on a non-zero exit. `--print-cron` emits the line to paste.

### What the screen shows

The thirteen lines open the lock file, try flock -n, and print the skip when another run holds it. On the fixture: SKIP backup: lock held, exit 75, then LOCK backup.lock.

### How to run it

`cron_wrapper.sh -n` backup `--timeout 900 --alert /usr/local/bin/page.sh` -- `/usr/local/bin/backup.sh`. Use `--print-cron` for the crontab line. Exit 0 is success, the command's code is passed through, 124 is the timeout, 75 is a skipped run, 2 is usage.

### The fix

Put the wrapper between cron and the job, and set the timeout below the interval. A twelve-minute job on a five-minute timer needs a lock, not a faster disk.

### Prevention

Watch exit 75. One skip a week is a warning that the job is growing; a skip every run means the timeout and the interval disagree.

> **The honest caveat:** flock is advisory, so a process that never opens the lock file can still write.

> **The lesson:** cron does not wait for the last run; the wrapper does.

## In one line

> **One lock, one writer.** Cron will start the next run whether or not the last one ended.

**Wrap the job:** `cron_wrapper.sh --name` backup -- job

## Script: cron_wrapper.sh

Download: [scripts/cron_wrapper.sh](../scripts/cron_wrapper.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# cron_wrapper.sh - run one cron job at a time, with a log, a timeout and an alert.
#
# Fixes: the 5-minute job that takes 12 minutes. The next run starts while the
# first still holds the data, both write, and neither knows. A second failure
# hides in the same place: the job dies, cron mails stdout to nobody, and the
# next run looks exactly like the last good one.
#
# The wrapper takes an exclusive flock before the command starts, stamps every
# log line, kills the command after --timeout seconds, and calls --alert on a
# non-zero exit. A run that cannot get the lock exits 75 without starting work.
#
# Usage:
#   cron_wrapper.sh --name backup --timeout 900 -- /usr/local/bin/backup.sh
#   cron_wrapper.sh --name backup --print-cron -- /usr/local/bin/backup.sh
#
# Cron (the line --print-cron emits, pasted into crontab -e):
#   */5 * * * * /usr/local/bin/cron_wrapper.sh --name backup \
#     --timeout 900 --alert /usr/local/bin/page.sh -- /usr/local/bin/backup.sh
#
# Exit codes:
#   0    the command finished successfully
#   1-125 the command's own exit code (124 means timeout killed it)
#   75   another run still holds the lock; nothing was started
#   2    usage error, missing tool, or an unwritable log/lock path
#
# Requires flock (util-linux), timeout (coreutils) and date. Tested with two
# overlapping runs on a fixture in /tmp; no real service is touched.
# By s0sta.com

PROG=${0##*/}
name=""
lock=""
log=""
timeout_s=3600
alert=""
schedule="*/5 * * * *"
print_cron=0
log_set=0
lock_set=0
run_tmp=""

usage() {
  cat <<'EOF'
cron_wrapper.sh - run one cron job at a time, with a log, a timeout and an alert

Usage:
  cron_wrapper.sh [options] -- COMMAND [ARGS...]

Options:
  -n, --name NAME   label for the log, lock and messages (default: command name)
  --lock FILE       lock file; default /run/lock/NAME.lock, or $TMPDIR if unwritable
  --log FILE        log file; default /var/log/NAME.log, or $TMPDIR if unwritable
  --timeout SECS    kill the command after SECS seconds; default 3600
  --alert CMD       executable called with one message when the command fails
  --schedule EXPR   five-field cron expression used by --print-cron
  --print-cron      print the crontab line and exit 0
  -h, --help        show this help and exit 0

The command must come after --. Example:
  cron_wrapper.sh --name backup --timeout 900 -- /usr/local/bin/backup.sh

Exit: 0 success, the command's code on failure, 124 timeout, 75 lock held.
EOF
}

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 2
}

# shellcheck disable=SC2329  # called by the EXIT trap
cleanup() {
  if [[ -n $run_tmp ]]; then
    rm -f -- "$run_tmp"
  fi
}
trap cleanup EXIT

ts() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

logline() {
  printf '%s %s\n' "$(ts)" "$1" >>"$log"
}

default_dir() {
  if [[ -d $1 && -w $1 ]]; then
    printf '%s' "$1"
  else
    printf '%s' "${TMPDIR:-/tmp}"
  fi
}

while (($#)); do
  case $1 in
    -n|--name)
      [[ $# -ge 2 ]] || die "--name needs a value"
      name=$2
      shift 2
      ;;
    --lock)
      [[ $# -ge 2 ]] || die "--lock needs a file"
      lock=$2
      lock_set=1
      shift 2
      ;;
    --log)
      [[ $# -ge 2 ]] || die "--log needs a file"
      log=$2
      log_set=1
      shift 2
      ;;
    --timeout)
      [[ $# -ge 2 ]] || die "--timeout needs a number of seconds"
      timeout_s=$2
      shift 2
      ;;
    --alert)
      [[ $# -ge 2 ]] || die "--alert needs an executable"
      alert=$2
      shift 2
      ;;
    --schedule)
      [[ $# -ge 2 ]] || die "--schedule needs five cron fields"
      schedule=$2
      shift 2
      ;;
    --print-cron)
      print_cron=1
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
      die "put the command after -- (try --help)"
      ;;
  esac
done

(($#)) || die "no command after -- (try --help)"

[[ $timeout_s =~ ^[0-9]+$ ]] || die "--timeout must be a whole number"
((timeout_s >= 1)) || die "--timeout must be at least 1"
IFS=' ' read -r -a sched_fields <<<"$schedule"
((${#sched_fields[@]} == 5)) || die "--schedule needs five fields"
if [[ -z $name ]]; then
  name=${1##*/}
fi
[[ -n $name ]] || die "cannot derive a name; use --name"
[[ $name =~ ^[A-Za-z0-9._-]+$ ]] || \
  die "--name may use letters, digits, dot, underscore and dash"

if [[ -z $lock ]]; then
  lock=$(default_dir /run/lock)/$name.lock
fi
if [[ -z $log ]]; then
  log=$(default_dir /var/log)/$name.log
fi
[[ $lock == /* ]] || die "--lock must be an absolute path"
[[ $log == /* ]] || die "--log must be an absolute path"

cmd_display=""
cron_cmd=""
for arg in "$@"; do
  cmd_display+="${cmd_display:+ }$arg"
  cron_cmd+="${cron_cmd:+ }$(printf '%q' "$arg")"
done

self=$0
if [[ $self != /* ]]; then
  self=$(cd "$(dirname "$self")" && pwd)/$(basename "$self")
fi
cron_line="$schedule $(printf '%q' "$self") --name $(printf '%q' "$name")"
cron_line+=" --timeout $timeout_s"
if [[ -n $alert ]]; then
  cron_line+=" --alert $(printf '%q' "$alert")"
fi
if ((log_set == 1)); then
  cron_line+=" --log $(printf '%q' "$log")"
fi
if ((lock_set == 1)); then
  cron_line+=" --lock $(printf '%q' "$lock")"
fi
cron_line+=" -- $cron_cmd"

if ((print_cron == 1)); then
  printf '%s\n' "$cron_line"
  exit 0
fi

command -v flock >/dev/null 2>&1 || die "flock is not installed (util-linux)"
command -v timeout >/dev/null 2>&1 || die "timeout is not installed (coreutils)"
if [[ $1 == */* ]]; then
  [[ -x $1 ]] || die "command is not executable: $1"
else
  command -v "$1" >/dev/null 2>&1 || die "command not found: $1"
fi
if [[ -n $alert ]]; then
  [[ $alert == /* ]] || die "--alert must be an absolute path"
  [[ -x $alert ]] || die "--alert is not executable: $alert"
fi

log_dir=${log%/*}
[[ -n $log_dir ]] || log_dir=/
lock_dir=${lock%/*}
[[ -n $lock_dir ]] || lock_dir=/
mkdir -p -- "$log_dir" || die "cannot create log directory: $log_dir"
mkdir -p -- "$lock_dir" || die "cannot create lock directory: $lock_dir"
if ! { : >>"$log"; } 2>/dev/null; then
  die "cannot write log file: $log"
fi
if ! { : >>"$lock"; } 2>/dev/null; then
  die "cannot write lock file: $lock"
fi

exec 9>>"$lock"
if ! flock -n 9; then
  printf 'SKIP %s: lock held, exit 75\n' "$name"
  printf 'LOCK %s\n' "${lock##*/}"
  logline "SKIP $name: another run holds $lock"
  exit 75
fi

logline "START $name: $cmd_display"
run_tmp=$(mktemp "${TMPDIR:-/tmp}/cron_wrapper.XXXXXX") || die "mktemp failed"
start=$(date +%s)

set +e
timeout --kill-after=10 "$timeout_s" "$@" >"$run_tmp" 2>&1
rc=$?
set -e

elapsed=$(( $(date +%s) - start ))
if [[ -s $run_tmp ]]; then
  stamped=$(ts)
  while IFS= read -r line || [[ -n $line ]]; do
    printf '%s %s\n' "$stamped" "$line" >>"$log"
  done <"$run_tmp"
fi
logline "END $name rc=$rc in ${elapsed}s"

if ((rc != 0)); then
  if ((rc == 124)); then
    msg="TIMEOUT $name killed after ${timeout_s}s"
  else
    msg="ALERT $name exited $rc after ${elapsed}s"
  fi
  logline "$msg"
  if [[ -n $alert ]]; then
    if ! "$alert" "$msg" >>"$log" 2>&1; then
      logline "ALERT hook failed: $alert"
    fi
  fi
  printf '%s\n' "$msg" >&2
  exit "$rc"
fi

logline "OK $name in ${elapsed}s"
exit 0
```
