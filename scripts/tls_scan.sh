#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
#
# tls_scan.sh - find hosts that still accept TLS 1.0, TLS 1.1 or a weak cipher.
#
# Fixes: TLS that is still offering 1.0. For every host:port it runs
# openssl s_client once for the certificate, then probes TLS 1.0, TLS 1.1
# and three legacy cipher suites. It prints the certificate's days to expiry
# and exits 1 when a weak protocol or cipher is accepted, or when a
# certificate is inside --warn-days.
#
# Usage:
#   tls_scan.sh api.example.com:443 mail.example.com:993
#   tls_scan.sh -f hosts.txt --warn-days 21 --timeout 4
#   tls_scan.sh --help
#
#   hosts.txt holds one host:port per line; blank lines and # comments are
#   ignored. IPv6 addresses are not supported in this version.
#
# Cron (daily, 04:20; exit 1 means a finding):
#   20 4 * * * /usr/local/sbin/tls_scan.sh -f /etc/s0sta/tls-hosts.txt \
#     >>/var/log/s0sta/tls-scan.log 2>&1
#
# Exit: 0 clean, 1 weak protocol/cipher or certificate inside --warn-days,
#       2 usage or unreadable input.
# Needs: openssl with s_client. timeout(1) is optional but recommended: on a
# host that blackholes the SYN, s_client can wait for the kernel timeout.
# By s0sta.com
#
usage() {
    cat <<'EOF'
tls_scan.sh - probe TLS 1.0, TLS 1.1 and legacy ciphers, and certificate expiry.

Usage:
  tls_scan.sh [OPTIONS] HOST:PORT ...
  tls_scan.sh -f FILE [OPTIONS]

  -f, --file FILE      read host:port entries from FILE
  -w, --warn-days N    warn when a certificate expires in fewer days (default 30)
  -t, --timeout N      seconds per connection (default 5)
  -h, --help           show this help and exit 0

Exit: 0 clean, 1 finding, 2 usage or unreadable input.
Read-only: openssl s_client only reads the handshake and the certificate.
EOF
}

die() {
    printf 'tls_scan: %s\n' "$1" >&2
    exit 2
}

WARN_DAYS=30
TIMEOUT=5
LIST_FILE=
TMP=$(mktemp -d "${TMPDIR:-/tmp}/tls_scan.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
: >"$TMP/targets"
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
        *) printf '%s\n' "$1" >>"$TMP/targets"; shift ;;
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
HELP=$(openssl s_client -help 2>&1 || true)
case "$HELP" in
    *-tls1*) ;;
    *) die "this openssl has no -tls1 option" ;;
esac

if [ -n "$LIST_FILE" ]; then
    [ -r "$LIST_FILE" ] || die "cannot read: $LIST_FILE"
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|\#*) continue ;;
        esac
        printf '%s\n' "$line" >>"$TMP/targets"
    done <"$LIST_FILE"
fi
[ -s "$TMP/targets" ] || die "no targets (give HOST:PORT or --file FILE)"

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
: >"$TMP/weak"
: >"$TMP/certs"
HOSTS=0
WEAK=0
CERTBAD=0

while IFS= read -r target; do
    [ -n "$target" ] || continue
    case "$target" in
        *:*) ;;
        *) die "not host:port: $target" ;;
    esac
    host=${target%:*}
    port=${target##*:}
    [ -n "$host" ] || die "empty host in: $target"
    case "$port" in
        ''|*[!0-9]*) die "bad port in: $target" ;;
    esac
    HOSTS=$((HOSTS + 1))

    cert=$(sclient -connect "$target" -servername "$host")
    end=$(printf '%s\n' "$cert" | openssl x509 -noout -enddate 2>/dev/null \
          | sed 's/^notAfter=//' || true)
    if [ -z "$end" ]; then
        printf 'ERROR %s no certificate returned\n' "$target" >>"$TMP/certs"
        CERTBAD=$((CERTBAD + 1))
    else
        epoch=$(to_epoch "$end")
        if [ -z "$epoch" ]; then
            printf 'ERROR %s cannot parse notAfter: %s\n' "$target" "$end" >>"$TMP/certs"
            CERTBAD=$((CERTBAD + 1))
        else
            days=$(( (epoch - NOW) / 86400 ))
            expires=$(fmt_date "$epoch")
            if [ "$epoch" -le "$NOW" ]; then
                printf 'EXPIRED %s certificate (%s)\n' \
                    "$target" "$expires" >>"$TMP/certs"
                CERTBAD=$((CERTBAD + 1))
            elif [ "$days" -lt "$WARN_DAYS" ]; then
                if [ "$days" -eq 0 ]; then
                    printf 'WARN %s certificate under 1 day (%s)\n' \
                        "$target" "$expires" >>"$TMP/certs"
                else
                    printf 'WARN %s certificate %d days (%s)\n' \
                        "$target" "$days" "$expires" >>"$TMP/certs"
                fi
                CERTBAD=$((CERTBAD + 1))
            else
                printf 'CERT %s %d days (%s)\n' \
                    "$target" "$days" "$expires" >>"$TMP/certs"
            fi
        fi
    fi

    for probe in -tls1 -tls1_1; do
        out=$(sclient -connect "$target" -servername "$host" "$probe")
        case "$out" in
            *"BEGIN CERTIFICATE"*)
                case "$probe" in
                    -tls1) label=TLSv1.0 ;;
                    *) label=TLSv1.1 ;;
                esac
                printf 'WEAK %s %s accepted\n' "$target" "$label" >>"$TMP/weak"
                WEAK=$((WEAK + 1)) ;;
        esac
    done

    for cipher in RC4-SHA DES-CBC3-SHA AES128-SHA; do
        out=$(sclient -connect "$target" -servername "$host" \
                      -tls1_2 -cipher "$cipher")
        case "$out" in
            *"BEGIN CERTIFICATE"*)
                printf 'WEAK %s cipher %s accepted\n' "$target" "$cipher" >>"$TMP/weak"
                WEAK=$((WEAK + 1)) ;;
        esac
    done
done <"$TMP/targets"

if [ "$WEAK" -eq 0 ] && [ "$CERTBAD" -eq 0 ]; then
    if [ "$HOSTS" -eq 1 ]; then
        printf 'OK 1 host, no weak protocol or expiring certificate\n'
    else
        printf 'OK %d hosts, no weak protocol or expiring certificate\n' "$HOSTS"
    fi
    exit 0
fi

if [ "$WEAK" -eq 0 ]; then
    printf 'FINDING no weak protocols\n'
elif [ "$WEAK" -eq 1 ]; then
    printf 'FINDING 1 weak protocol accepted\n'
else
    printf 'FINDING %d weak protocols accepted\n' "$WEAK"
fi
cat "$TMP/weak"
cat "$TMP/certs"

exit 1
