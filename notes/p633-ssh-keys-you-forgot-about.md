---
id: p633
title: "SSH keys you forgot about"
slug: ssh-keys-you-forgot-about
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, SSH, CyberSecurity, SysAdmin]
source: "LinkedIn post P633 · ShellSec series"
linkedin_date: 2030-10-13
design: code
script: ssh_key_audit.sh
---

# SSH keys you forgot about

A contractor left in March. In October their key still opens the jump host, because it sits on line 3 of an authorized_keys file nobody has read since the account was created.

## Quick reference

The full script is at the end of this note: `ssh_key_audit.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash ssh_key_audit.sh /home/ana
```

**Example output**

```text
FINDING 2 issues in 3 keys
WEAK ssh-rsa .ssh/authorized_keys:2
```

## Explained

### What it does

`ssh_key_audit.sh` scans `/home/*/.ssh/authorized_keys` and `/root/.ssh`. It checks the mode on .ssh and the file, flags ssh-dss and ssh-rsa keys, keys with no comment, unparsable lines and duplicate public keys. It never prints a key blob.

### What the screen shows

The fourteen lines read one authorized_keys file, count the keys, write WEAK and NOCOMMENT lines to a temp list, then print the summary and the first hit. On the fixture: FINDING 2 issues in 3 keys and WEAK ssh-rsa .ssh/authorized_keys:2.

### How to run it

bash `ssh_key_audit.sh /home /root`. The Monday cron line is 40 6 \* \* 1. Exit 0 is clean, 1 is a finding, 2 is an unreadable path. It writes nothing outside its temp directory.

### The fix

Remove the flagged key, then rotate the account it belonged to. A key removed without a rotation may already have been copied. Replace ssh-rsa and ssh-dss with ed25519, and give every replacement a comment with an owner and a ticket.

### Prevention

Review keys when someone leaves, not once a year. Put the expected keys in configuration management and let the audit diff against that list.

> **The honest caveat:** modes and key types are only part of the story. sshd StrictModes also checks the home directory.

> **The lesson:** an authorized key is a password that never expires.

## In one line

> **A key is a permanent password.** It has no expiry, no lockout and no second factor.

**Count the keys:** `ssh_key_audit.sh /home /root`

## Script: ssh_key_audit.sh

Download: [scripts/ssh_key_audit.sh](../scripts/ssh_key_audit.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
#
# ssh_key_audit.sh - audit authorized_keys files without printing key material.
#
# Fixes: the SSH keys you forgot about. Scans /home/*/.ssh/authorized_keys
# and /root/.ssh/authorized_keys for:
#   LOOSE      .ssh or authorized_keys writable by group or other
#   WEAK       ssh-dss or ssh-rsa keys (DSA, and RSA restricted to SHA-1)
#   NOCOMMENT  a key with no comment, so nobody can say whose it is
#   UNPARSED   a line that is not a key and not a comment
#   DUP        the same public key installed more than once
# It reads public keys only. The output never contains a key blob or a
# private key, and the script writes nothing outside its temporary directory.
# sshd's StrictModes also checks the home directory; this audits .ssh and
# authorized_keys, not every parent directory.
#
# Usage:
#   ssh_key_audit.sh                     # /home and /root
#   ssh_key_audit.sh /home /root         # explicit roots
#   ssh_key_audit.sh /tmp/fixture/home   # test tree
#   ssh_key_audit.sh --help
#
# Cron (Mondays, 06:40; exit 1 means findings):
#   40 6 * * 1 /usr/local/sbin/ssh_key_audit.sh /home /root \
#     >>/var/log/s0sta/ssh-keys.log 2>&1
#
# Exit: 0 no findings, 1 findings, 2 usage or unreadable input.
# Needs: find, stat (GNU or BSD), awk. No ssh-keygen required.
# By s0sta.com
#
usage() {
    cat <<'EOF'
ssh_key_audit.sh - audit authorized_keys files.

Usage:
  ssh_key_audit.sh [ROOT ...]
  ssh_key_audit.sh --help

  ROOT   a home directory, a tree of homes, or an authorized_keys file
         (default: /home /root)

Exit: 0 no findings, 1 findings, 2 usage or unreadable input.
Read-only: public keys are read, nothing is changed.
EOF
}

die() {
    printf 'ssh_key_audit: %s\n' "$1" >&2
    exit 2
}

mode_of() {
    stat -c '%a' "$1" 2>/dev/null || stat -f '%Lp' "$1" 2>/dev/null || true
}

# True when group or other has a write bit (2, 3, 6 or 7 in either place).
is_loose() {
    local m g o
    m=$(mode_of "$1")
    [ -n "$m" ] || return 1
    g=${m: -2:1}
    o=${m: -1:1}
    case "${g}${o}" in
        *[2367]*) return 0 ;;
    esac
    return 1
}

[ "$#" -gt 0 ] || set -- /home /root
for arg in "$@"; do
    case "$arg" in
        -h|--help) usage; exit 0 ;;
        -*) die "unknown argument: $arg" ;;
    esac
done

TMP=$(mktemp -d "${TMPDIR:-/tmp}/ssh_key_audit.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
: >"$TMP/files"
for root in "$@"; do
    [ -r "$root" ] || die "cannot read: $root"
    if [ -f "$root" ]; then
        printf '%s\n' "$root" >>"$TMP/files"
    elif [ -d "$root" ]; then
        find "$root" -maxdepth 3 -type f -name authorized_keys -print \
            2>/dev/null >>"$TMP/files" || true
    else
        die "not a file or directory: $root"
    fi
done
sort -u "$TMP/files" -o "$TMP/files"

if [ ! -s "$TMP/files" ]; then
    printf 'OK no authorized_keys found under: %s\n' "$*"
    exit 0
fi

: >"$TMP/loose"
: >"$TMP/weak"
: >"$TMP/nocomment"
: >"$TMP/unparsed"
: >"$TMP/keys"
KEYS=0
FILES=0

while IFS= read -r keyfile; do
    [ -n "$keyfile" ] || continue
    FILES=$((FILES + 1))
    sshdir=$(dirname "$keyfile")
    if is_loose "$sshdir"; then
        printf 'LOOSE %s %s\n' "$sshdir" "$(mode_of "$sshdir")" >>"$TMP/loose"
    fi
    if is_loose "$keyfile"; then
        printf 'LOOSE %s %s\n' "$keyfile" "$(mode_of "$keyfile")" >>"$TMP/loose"
    fi

    lineno=0
    while IFS= read -r line || [ -n "$line" ]; do
        lineno=$((lineno + 1))
        case "$line" in
            ''|\#*) continue ;;
        esac
        # authorized_keys may start with options; brackets are not valid in
        # base64, so the first field that looks like a key type wins.
        IFS=' ' read -r -a fields <<<"$line"
        type=
        blob=
        idx=0
        while [ "$idx" -lt "${#fields[@]}" ]; do
            case "${fields[$idx]}" in
                ssh-*|ecdsa-sha2-*|sk-*) type=${fields[$idx]}; break ;;
            esac
            idx=$((idx + 1))
        done
        if [ -z "$type" ] || [ "$((idx + 1))" -ge "${#fields[@]}" ]; then
            printf 'UNPARSED %s:%s\n' "$keyfile" "$lineno" >>"$TMP/unparsed"
            continue
        fi
        blob=${fields[$((idx + 1))]}
        [ -n "$blob" ] || {
            printf 'UNPARSED %s:%s\n' "$keyfile" "$lineno" >>"$TMP/unparsed"
            continue
        }
        KEYS=$((KEYS + 1))
        printf '%s %s:%s\n' "$blob" "$keyfile" "$lineno" >>"$TMP/keys"
        case "$type" in
            ssh-dss*|ssh-rsa*)
                printf 'WEAK %s %s:%s\n' "$type" "$keyfile" "$lineno" >>"$TMP/weak" ;;
        esac
        comment=
        j=$((idx + 2))
        while [ "$j" -lt "${#fields[@]}" ]; do
            comment="$comment ${fields[$j]}"
            j=$((j + 1))
        done
        if [ -z "$comment" ]; then
            printf 'NOCOMMENT %s:%s\n' "$keyfile" "$lineno" >>"$TMP/nocomment"
        fi
    done <"$keyfile"
done <"$TMP/files"

awk '{ c[$1]++; loc[$1] = loc[$1] " " $2 }
     END { for (k in c) if (c[k] > 1) printf "DUP %d%s\n", c[k], loc[k] }' \
    "$TMP/keys" | LC_ALL=C sort >"$TMP/dup"

LOOSE=$(wc -l <"$TMP/loose" || true)
WEAK=$(wc -l <"$TMP/weak" || true)
NOCOMMENT=$(wc -l <"$TMP/nocomment" || true)
UNPARSED=$(wc -l <"$TMP/unparsed" || true)
DUP=$(wc -l <"$TMP/dup" || true)
ISSUES=$((LOOSE + WEAK + NOCOMMENT + UNPARSED + DUP))

if [ "$KEYS" -eq 1 ]; then
    k=key
else
    k=keys
fi
if [ "$FILES" -eq 1 ]; then
    f='file'
else
    f='files'
fi
if [ "$ISSUES" -eq 1 ]; then
    i=issue
else
    i=issues
fi

if [ "$ISSUES" -eq 0 ]; then
    printf 'OK %d %s in %d %s, no issues\n' "$KEYS" "$k" "$FILES" "$f"
    exit 0
fi

printf 'FINDING %d %s in %d %s\n' "$ISSUES" "$i" "$KEYS" "$k"
cat "$TMP/loose"
cat "$TMP/weak"
cat "$TMP/nocomment"
cat "$TMP/unparsed"
cat "$TMP/dup"

exit 1
```
