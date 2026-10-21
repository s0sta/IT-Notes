---
id: p625
title: "Services that died quietly"
slug: services-that-died-quietly
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, Systemd, SRE, DevOps]
source: "LinkedIn post P625 · ShellSec series"
linkedin_date: 2030-09-24
design: code
script: service_health.sh
---

# Services that died quietly

A service failed at 02:00 and systemd restarted it. By 08:00 the restart counter read 412, and every dashboard scrape had caught the unit active. Nothing was green; the samples were.

## Quick reference

The full script is at the end of this note: `service_health.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash service_health.sh --units /tmp/p625/units.txt
```

**Example output**

```text
FINDING 1 service problem
ALERT api.service failed
```

## Explained

### What it does

`service_health.sh` reads `systemctl list-units --failed` and systemctl show properties: ActiveState, SubState, UnitFileState and NRestarts. It reports three classes: a failed unit, a unit restarted at least `--restarts` times (3 by default), and an enabled unit that is inactive. It never restarts anything.

### What the screen shows

The thirteen lines in the GIF read the captured failed list, keep the service units, and print the count and the first failed unit. On the fixture: FINDING 1 service problem and ALERT `api.service` failed.

### How to run it

bash `service_health.sh`, or pass `--units` and `--props` captures from a host you cannot reach. Exit 0 is clean, 1 is a finding, 2 is usage or an unreadable file. The cron line is `45 6 * * * /usr/local/bin/service_health.sh`.

### The fix

Read `journalctl -u api.service --since '30` min ago' before you touch it. Fix the cause, then systemctl reset-failed `api.service` so the next failure starts clean. For a restart loop, cap it with StartLimitBurst and StartLimitIntervalSec instead of letting it spin.

### Prevention

Alert on the NRestarts delta and on ActiveState=failed, not only on the unit being inactive. A restart is a recovery attempt, not a recovery.

> **The honest caveat:** NRestarts counts automatic restarts since the last reset, so it measures the recent past, not the year.

> **The lesson:** active is a state, while healthy is a history.

## In one line

> **A restart is not a recovery.** Count restarts, not just the state at the last scrape.

**Read the unit**

```bash
systemctl status api --no-pager
```

## Script: service_health.sh

Download: [scripts/service_health.sh](../scripts/service_health.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# service_health.sh - find the services that died quietly.
# Fixes: a failed unit, a unit the manager keeps restarting, and an enabled
#        unit that is inactive. Read-only: it never starts, stops or restarts.
#
# Usage:
#   service_health.sh [options]
#   service_health.sh --units /tmp/failed.txt --props /tmp/show.txt
#
# Options:
#   --units FILE    captured `systemctl list-units --failed` output
#   --props FILE    captured `systemctl show` output (Id, ActiveState,
#                   SubState, UnitFileState, NRestarts)
#   --restarts N    flag a unit with N or more restarts (default 3)
#   -h, --help      show this help and exit 0
#
# With no --units and no --props the script reads systemctl directly.
# Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
# Needs: systemd (systemctl), awk, sort. Linux.
# Cron: 45 6 * * * /usr/local/bin/service_health.sh
# By s0sta.com

usage() {
    cat <<'EOF'
service_health.sh - find the services that died quietly.

Usage:
  service_health.sh [options]
  service_health.sh --units /tmp/failed.txt --props /tmp/show.txt

Options:
  --units FILE    captured `systemctl list-units --failed` output
  --props FILE    captured `systemctl show` output (Id, ActiveState,
                  SubState, UnitFileState, NRestarts)
  --restarts N    flag a unit with N or more restarts (default 3)
  -h, --help      show this help and exit 0

Reports failed units, auto-restarting units and enabled-but-inactive units.
Read-only.
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

units_file=""
props_file=""
min_restarts=3

while [ "$#" -gt 0 ]; do
    case "$1" in
        --units)    [ "$#" -ge 2 ] || die "missing value for $1"; units_file=$2; shift 2 ;;
        --props)    [ "$#" -ge 2 ] || die "missing value for $1"; props_file=$2; shift 2 ;;
        --restarts) [ "$#" -ge 2 ] || die "missing value for $1"; min_restarts=$2; shift 2 ;;
        -h|--help)  usage; exit 0 ;;
        *)          die "unknown option: $1 (try --help)" ;;
    esac
done

is_number "$min_restarts" || die "not a number: $min_restarts"
if [ -n "$units_file" ]; then
    [ -r "$units_file" ] || die "cannot read units file: $units_file"
fi
if [ -n "$props_file" ]; then
    [ -r "$props_file" ] || die "cannot read props file: $props_file"
fi

if [ -z "$units_file" ] && [ -z "$props_file" ]; then
    command -v systemctl >/dev/null 2>&1 || die "systemctl not found; pass --units/--props"
    units_out=$(systemctl list-units --failed --no-legend --plain --type=service) \
        || die "systemctl list-units failed"
    props_out=$(systemctl show --all --type=service \
        -p Id -p ActiveState -p SubState -p UnitFileState -p NRestarts) \
        || die "systemctl show failed"
else
    units_out=""
    props_out=""
    [ -z "$units_file" ] || units_out=$(cat "$units_file")
    [ -z "$props_file" ] || props_out=$(cat "$props_file")
fi

ids=()
actives=()
subs=()
ufiles=()
restart_counts=()

add_unit() {
    local i
    i=0
    while [ "$i" -lt "${#ids[@]}" ]; do
        if [ "${ids[$i]}" = "$1" ]; then
            actives[i]=$2
            subs[i]=$3
            ufiles[i]=$4
            restart_counts[i]=$5
            return 0
        fi
        i=$((i + 1))
    done
    ids+=("$1")
    actives+=("$2")
    subs+=("$3")
    ufiles+=("$4")
    restart_counts+=("$5")
    return 0
}

if [ -n "$props_out" ]; then
    id=""
    active=""
    sub=""
    ufile=""
    nrestarts=0
    flush_unit() {
        if [ -n "$id" ]; then
            add_unit "$id" "${active:-unknown}" "${sub:-unknown}" "${ufile:-unknown}" "${nrestarts:-0}"
        fi
        id=""
        active=""
        sub=""
        ufile=""
        nrestarts=0
        return 0
    }
    while IFS= read -r line; do
        case "$line" in
            Id=*)            id=${line#Id=} ;;
            ActiveState=*)   active=${line#ActiveState=} ;;
            SubState=*)      sub=${line#SubState=} ;;
            UnitFileState=*) ufile=${line#UnitFileState=} ;;
            NRestarts=*)     nrestarts=${line#NRestarts=} ;;
            '')              flush_unit ;;
        esac
    done <<< "$props_out"
    flush_unit
fi

mark_failed() {
    local i
    i=0
    while [ "$i" -lt "${#ids[@]}" ]; do
        if [ "${ids[$i]}" = "$1" ]; then
            actives[i]=failed
            return 0
        fi
        i=$((i + 1))
    done
    add_unit "$1" failed unknown unknown 0
    return 0
}

if [ -n "$units_out" ]; then
    while IFS= read -r line; do
        line=${line#"${line%%[![:space:]]*}"}
        unit=${line%% *}
        case "$unit" in
            *.service) ;;
            *) continue ;;
        esac
        mark_failed "$unit"
    done <<< "$units_out"
fi

failed_list=()
restart_list=()
inactive_list=()

if [ "${#ids[@]}" -gt 0 ]; then
for i in "${!ids[@]}"; do
    id=${ids[$i]}
    active=${actives[$i]}
    sub=${subs[$i]}
    ufile=${ufiles[$i]}
    nrestarts=${restart_counts[$i]}

    if [ "$active" = failed ]; then
        failed_list+=("$id|$active|$sub|$nrestarts")
    elif is_number "$nrestarts" && [ "$nrestarts" -ge "$min_restarts" ]; then
        restart_list+=("$id|$nrestarts")
    elif [ "$ufile" = enabled ] && [ "$active" = inactive ]; then
        inactive_list+=("$id")
    fi
done
fi

count=$(( ${#failed_list[@]} + ${#restart_list[@]} + ${#inactive_list[@]} ))
if [ "$count" -eq 1 ]; then
    label=problem
else
    label=problems
fi
printf 'FINDING %d service %s\n' "$count" "$label"

if [ "$count" -gt 0 ]; then
    if [ "${#failed_list[@]}" -gt 0 ]; then
        first=${failed_list[0]}
        IFS='|' read -r fid _ _ _ <<< "$first"
        printf 'ALERT %s failed\n' "$fid"
    elif [ "${#restart_list[@]}" -gt 0 ]; then
        first=${restart_list[0]}
        IFS='|' read -r rid rnum <<< "$first"
        printf 'ALERT %s restarted %s times\n' "$rid" "$rnum"
    else
        printf 'ALERT %s enabled but inactive\n' "${inactive_list[0]}"
    fi
fi

if [ "${#failed_list[@]}" -gt 0 ]; then
    printf '%s\n' "${failed_list[@]}" | while IFS='|' read -r id active sub _; do
        printf 'FAILED %s (%s/%s)\n' "$id" "$active" "$sub"
    done
fi
if [ "${#restart_list[@]}" -gt 0 ]; then
    printf '%s\n' "${restart_list[@]}" | while IFS='|' read -r id nrestarts; do
        printf 'RESTARTING %s restarts=%s\n' "$id" "$nrestarts"
    done
fi
if [ "${#inactive_list[@]}" -gt 0 ]; then
    printf '%s\n' "${inactive_list[@]}" | while IFS= read -r id; do
        printf 'INACTIVE-ENABLED %s enabled but inactive\n' "$id"
    done
fi

if [ "$count" -gt 0 ]; then
    exit 1
fi
exit 0
```
