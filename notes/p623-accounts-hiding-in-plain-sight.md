---
id: p623
title: "Accounts hiding in plain sight"
slug: accounts-hiding-in-plain-sight
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, CyberSecurity, SysAdmin, DevSecOps]
source: "LinkedIn post P623 · ShellSec series"
linkedin_date: 2030-09-19
design: code
script: user_audit.sh
---

# Accounts hiding in plain sight

The access review said twelve administrators. `/etc/passwd` had thirteen accounts with UID 0, and the extra one had a home directory nobody recognised.

## Quick reference

The full script is at the end of this note: `user_audit.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash user_audit.sh --passwd /tmp/p623/passwd
```

**Example output**

```text
FINDING 2 account risks
ALERT uid 0: toor (/bin/bash)
```

## Explained

### What it does

`user_audit.sh` reads `/etc/passwd` and, when you pass `--shadow`, a shadow export. It flags four things: a second UID 0 account, an empty password field, an expired account or password, and a system account with a login shell. `--today` fixes the date so a test is repeatable.

### What the screen shows

The fourteen lines in the GIF read the passwd file, catch UID 0 accounts and service accounts with a real shell, then print the count and the first risk. On the fixture: FINDING 2 account risks and ALERT uid 0: toor (`/bin/bash`).

### How to run it

bash `user_audit.sh --passwd /etc/passwd`, then add `--shadow /root/shadow.export`. Exit 0 is clean, 1 is a finding, 2 is usage or an unreadable file. Run it weekly from cron.

### The fix

A second UID 0 account is either a mistake or a backdoor. Lock it, log it, and remove it after the change window. Replace a service account's shell with `/usr/sbin/nologin`. Lock an empty password with `passwd -l`, and expire the account with `chage -E 0`.

### Prevention

Keep a known-good list of UID 0 accounts and login shells in version control, and diff it in the image and on the host.

> **The honest caveat:** a shadow field of ! or \* means locked, not empty; only a truly empty field is reported.

> **The lesson:** a login shell is a door, and a system account rarely needs one.

## In one line

> **UID 0 is a shared secret.** A login shell on a system account is a door left open.

**Audit the host:** bash `user_audit.sh --passwd /etc/passwd`

## Script: user_audit.sh

Download: [scripts/user_audit.sh](../scripts/user_audit.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# user_audit.sh - find the accounts that should not be able to log in.
# Fixes: a second UID 0 account, an empty password field, an expired account,
#        and a service account with a login shell. Read-only.
#
# Usage:
#   user_audit.sh [options]
#   user_audit.sh --shadow /root/shadow.export --today 2026-10-21
#
# Options:
#   --passwd FILE   passwd file to read (default /etc/passwd)
#   --shadow FILE   shadow export to read (default: none; needs root)
#   --today DATE    treat DATE as today, YYYY-MM-DD (default: system date)
#   -h, --help      show this help and exit 0
#
# Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
# Needs: awk, date. Linux; /etc/shadow is usually readable by root only, so
#        export it first: getent shadow > /root/shadow.export
# Cron: 15 6 * * 1 /usr/local/bin/user_audit.sh --shadow /root/shadow.export
# By s0sta.com

usage() {
    cat <<'EOF'
user_audit.sh - find the accounts that should not be able to log in.

Usage:
  user_audit.sh [options]
  user_audit.sh --shadow /root/shadow.export --today 2026-10-21

Options:
  --passwd FILE   passwd file to read (default /etc/passwd)
  --shadow FILE   shadow export to read (default: none; needs root)
  --today DATE    treat DATE as today, YYYY-MM-DD (default: system date)
  -h, --help      show this help and exit 0

Checks: UID 0 accounts other than root, empty password fields, expired
accounts (password and account expiry), and system accounts with a login
shell. Read-only.
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

passwd_file=/etc/passwd
shadow_file=""
today=""
details=()
alert=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --passwd)  [ "$#" -ge 2 ] || die "missing value for $1"; passwd_file=$2; shift 2 ;;
        --shadow)  [ "$#" -ge 2 ] || die "missing value for $1"; shadow_file=$2; shift 2 ;;
        --today)   [ "$#" -ge 2 ] || die "missing value for $1"; today=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *)         die "unknown option: $1 (try --help)" ;;
    esac
done

[ -r "$passwd_file" ] || die "cannot read passwd file: $passwd_file"
if [ -n "$shadow_file" ]; then
    [ -r "$shadow_file" ] || die "cannot read shadow file: $shadow_file"
fi

if [ -n "$today" ]; then
    case "$today" in
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
        *) die "bad --today, want YYYY-MM-DD: $today" ;;
    esac
    if date -d "$today" +%s >/dev/null 2>&1; then
        epoch=$(date -d "$today" +%s)
    elif epoch=$(date -j -f "%Y-%m-%d" "$today" +%s 2>/dev/null); then
        :
    else
        die "cannot parse date: $today"
    fi
else
    epoch=$(date +%s)
fi
today_days=$((epoch / 86400))

add_finding() {
    details+=("$1")
    if [ -z "$alert" ]; then
        alert=$2
    fi
}

while IFS=: read -r name pw uid _ _ home shell; do
    case "$name" in
        ''|'#'*) continue ;;
    esac

    if [ "$uid" = 0 ] && [ "$name" != root ]; then
        add_finding "UID0 $name shell=$shell home=$home" "uid 0: $name ($shell)"
    fi

    if [ -z "$pw" ]; then
        add_finding "EMPTY-PW $name passwd password field empty" "empty password: $name"
    fi

    if [ -n "$shadow_file" ]; then
        sline=$(awk -F: -v u="$name" '$1 == u { print; exit }' "$shadow_file")
        if [ -n "$sline" ]; then
            IFS=: read -r _ spw slast _ smax _ _ sexpire _ <<< "$sline"

            if [ -z "$spw" ]; then
                add_finding "EMPTY-PW $name shadow password field empty" "empty password: $name"
            fi

            if is_number "$sexpire" && [ "$sexpire" -gt 0 ] && [ "$sexpire" -le "$today_days" ]; then
                ago=$((today_days - sexpire))
                add_finding "EXPIRED $name account expired ${ago}d ago" "expired account: $name"
            fi

            if is_number "$slast" && is_number "$smax" && [ "$slast" -gt 0 ] \
                && [ "$smax" -gt 0 ] && [ "$smax" -ne 99999 ]; then
                pw_end=$((slast + smax))
                if [ "$pw_end" -lt "$today_days" ]; then
                    ago=$((today_days - pw_end))
                    add_finding "EXPIRED $name password expired ${ago}d ago" "expired account: $name"
                fi
            fi
        fi
    fi

    if is_number "$uid" && [ "$uid" -lt 1000 ] && [ "$uid" -ne 0 ]; then
        case "$shell" in
            ''|*/nologin|*/false|/bin/sync|/sbin/shutdown|/sbin/halt) ;;
            *) add_finding "SHELL $name shell=$shell uid=$uid" "service shell: $name ($shell)" ;;
        esac
    fi
done < "$passwd_file"

if [ "${#details[@]}" -eq 1 ]; then
    label=risk
else
    label=risks
fi
printf 'FINDING %d account %s\n' "${#details[@]}" "$label"
if [ -n "$alert" ]; then
    printf 'ALERT %s\n' "$alert"
fi
if [ "${#details[@]}" -gt 0 ]; then
    printf '%s\n' "${details[@]}"
    exit 1
fi
exit 0
```
