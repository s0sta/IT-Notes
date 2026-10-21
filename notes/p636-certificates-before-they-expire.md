---
id: p636
title: "Certificates before they expire"
slug: certificates-before-they-expire
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, TLS, PKI, DevOps, SRE]
source: "LinkedIn post P636 · ShellSec series"
linkedin_date: 2030-10-20
design: code
script: cert_renew_check.sh
---

# Certificates before they expire

The leaf expires at 09:00 on a Saturday. Monitoring says the endpoint is fine, because the load balancer still serves a valid certificate from another node.

## Quick reference

The full script is at the end of this note: `cert_renew_check.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash cert_renew_check.sh certs.txt 30
```

**Example output**

```text
EXPIRED old.example.com.pem -2 days
FINDING 1 certificate warning
```

## Explained

### What it does

`cert_renew_check.sh` reads host:port entries and PEM paths. Hosts go through openssl s_client, files through openssl x509. It prints days to expiry, flags anything inside `--warn-days`, and marks an expired certificate with a negative count. Exit 1 means action.

### What the screen shows

The fourteen lines read the list, load a PEM or open a socket, parse notAfter, subtract now, then print the status and the count: EXPIRED `old.example.com.pem -2` days and FINDING 1 certificate warning.

### How to run it

bash `cert_renew_check.sh -f certs.txt --warn-days 30`. The cron line runs at 05:10 daily. Exit 0 is clean, 1 is a warning or expired certificate, 2 is an unreadable file or a host with no certificate.

### The fix

Renew at 30 days, deploy at 14, and verify the mounted file on every node, not just the one monitoring probes. A certificate renewed in one place and pinned in another is two problems.

### Prevention

Keep one list in Git, add a host when it joins the load balancer, and run the check after every deploy. The list is the inventory; the scan is the proof.

> **The honest caveat:** a bundle is read at its first certificate. Chain order, signatures and key matches need openssl verify, which this script does not run.

> **The lesson:** a certificate does not expire when you remember. It expires when the clock says.

## In one line

> **Renew on the number, not the date.** A calendar reminder is a hope; a day count is a check.

**Check the list:** `cert_renew_check.sh -f certs.txt`

## Script: cert_renew_check.sh

Download: [scripts/cert_renew_check.sh](../scripts/cert_renew_check.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
#
# cert_renew_check.sh - days to expiry for host:port endpoints and PEM files.
#
# Fixes: certificates before they expire. Reads a list of host:port entries
# or PEM file paths, prints the days to expiry for each one, flags anything
# inside --warn-days, and flags an expired certificate as EXPIRED. A negative
# day count means the certificate expired that many days ago.
#
# Usage:
#   cert_renew_check.sh -f certs.txt
#   cert_renew_check.sh -f certs.txt --warn-days 21 --timeout 4
#   cert_renew_check.sh api.example.com:443 /etc/ssl/certs/api.pem
#   cert_renew_check.sh --help
#
#   certs.txt holds one host:port or one PEM path per line; blank lines and
#   # comments are ignored. A PEM bundle is read at its first certificate.
#   IPv6 addresses are not supported in this version.
#
# Cron (daily, 05:10; exit 1 means a finding):
#   10 5 * * * /usr/local/sbin/cert_renew_check.sh -f /etc/s0sta/certs.txt \
#     --warn-days 30 >>/var/log/s0sta/cert-renew.log 2>&1
#
# Exit: 0 clean, 1 certificate inside --warn-days or expired, 2 usage or
#       unreadable input (including a host that returns no certificate).
# Needs: openssl with x509 and s_client. timeout(1) is optional but
# recommended for host entries that blackhole the SYN.
# Read-only: certificates are read; no key file is opened or printed.
# By s0sta.com
#
usage() {
    cat <<'EOF'
cert_renew_check.sh - report certificate expiry for hosts and PEM files.

Usage:
  cert_renew_check.sh [OPTIONS] [HOST:PORT|FILE ...]
  cert_renew_check.sh -f FILE [OPTIONS]

  -f, --file FILE      read host:port or PEM paths from FILE
  -w, --warn-days N    warn inside this many days (default 30)
  -t, --timeout N      seconds per TLS connection (default 5)
  -h, --help           show this help and exit 0

Exit: 0 clean, 1 warning or expired, 2 usage or unreadable input.
Read-only: no private key is read or printed.
EOF
}

die() {
    printf 'cert_renew_check: %s\n' "$1" >&2
    exit 2
}

WARN_DAYS=30
TIMEOUT=5
LIST_FILE=
TMP=$(mktemp -d "${TMPDIR:-/tmp}/cert_renew_check.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
: >"$TMP/entries"
while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        -f|--file)
            [ "$#" -ge 2 ] || die "--file needs a path"
            LIST_FILE=$2; shift 2 ;;
        -w|--warn-days)
            [ "$#" -ge 2 ] || die "--warn-days needs a number"
            WARN_DAYS=$2; shift 2 ;;
        -t|--timeout)
            [ "$#" -ge 2 ] || die "--timeout needs a number"
            TIMEOUT=$2; shift 2 ;;
        -*) die "unknown argument: $1" ;;
        *) printf '%s\n' "$1" >>"$TMP/entries"; shift ;;
    esac
done

case "$WARN_DAYS" in
    ''|*[!0-9]*) die "--warn-days must be a whole number" ;;
esac
case "$TIMEOUT" in
    ''|*[!0-9]*) die "--timeout must be a whole number" ;;
esac
[ "$TIMEOUT" -ge 1 ] || die "--timeout must be at least 1"
command -v openssl >/dev/null 2>&1 || die "openssl not found"

if [ -n "$LIST_FILE" ]; then
    [ -r "$LIST_FILE" ] || die "cannot read: $LIST_FILE"
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|\#*) continue ;;
        esac
        printf '%s\n' "$line" >>"$TMP/entries"
    done <"$LIST_FILE"
fi
[ -s "$TMP/entries" ] || die "no entries (give HOST:PORT, FILE or --file FILE)"

TMO=
if command -v timeout >/dev/null 2>&1; then
    TMO=timeout
elif command -v gtimeout >/dev/null 2>&1; then
    TMO=gtimeout
fi

sclient() {
    if [ -n "$TMO" ]; then
        "$TMO" "$TIMEOUT" openssl s_client "$@" </dev/null 2>/dev/null || true
    else
        openssl s_client "$@" </dev/null 2>/dev/null &
        local pid=$! wd
        ( sleep "$TIMEOUT"; kill -TERM "$pid" 2>/dev/null || true ) &
        wd=$!
        wait "$pid" 2>/dev/null || true
        kill -TERM "$wd" 2>/dev/null || true
        wait "$wd" 2>/dev/null || true
    fi
    return 0
}

to_epoch() {
    local s
    s=$(printf '%s' "$1" | tr -s ' ')
    if date -u -d "$s" +%s >/dev/null 2>&1; then
        date -u -d "$s" +%s
    else
        date -u -j -f "%b %d %T %Y %Z" "$s" +%s 2>/dev/null || true
    fi
}

fmt_date() {
    if date -u -d "@$1" +%F >/dev/null 2>&1; then
        date -u -d "@$1" +%F
    else
        date -u -r "$1" +%F 2>/dev/null || true
    fi
}

NOW=$(date -u +%s)
BAD=0
RC=0

while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    end=
    if [ -f "$entry" ]; then
        end=$(openssl x509 -in "$entry" -noout -enddate 2>/dev/null \
              | sed 's/^notAfter=//' || true)
    else
        case "$entry" in
            *:*) ;;
            *) die "not a file or host:port: $entry" ;;
        esac
        host=${entry%:*}
        port=${entry##*:}
        [ -n "$host" ] || die "empty host in: $entry"
        case "$port" in
            ''|*[!0-9]*) die "bad port in: $entry" ;;
        esac
        cert=$(sclient -connect "$entry" -servername "$host")
        end=$(printf '%s\n' "$cert" | openssl x509 -noout -enddate 2>/dev/null \
              | sed 's/^notAfter=//' || true)
    fi
    if [ -z "$end" ]; then
        printf 'ERROR %s no certificate\n' "$entry"
        RC=2
        continue
    fi
    epoch=$(to_epoch "$end")
    if [ -z "$epoch" ]; then
        printf 'ERROR %s cannot parse notAfter: %s\n' "$entry" "$end"
        RC=2
        continue
    fi
    days=$(( (epoch - NOW) / 86400 ))
    expires=$(fmt_date "$epoch")
    if [ "$epoch" -le "$NOW" ]; then
        printf 'EXPIRED %s %d days (%s)\n' "$entry" "$days" "$expires"
        BAD=$((BAD + 1))
    elif [ "$days" -lt "$WARN_DAYS" ]; then
        printf 'WARN %s %d days (%s)\n' "$entry" "$days" "$expires"
        BAD=$((BAD + 1))
    else
        printf 'OK %s %d days (%s)\n' "$entry" "$days" "$expires"
    fi
done <"$TMP/entries"

if [ "$BAD" -eq 1 ]; then
    printf 'FINDING 1 certificate warning\n'
elif [ "$BAD" -gt 1 ]; then
    printf 'FINDING %d certificate warnings\n' "$BAD"
elif [ "$RC" -eq 0 ]; then
    printf 'OK no certificate inside %d days\n' "$WARN_DAYS"
fi

[ "$RC" -eq 0 ] || exit 2
[ "$BAD" -eq 0 ] || exit 1
exit 0
```
