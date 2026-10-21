#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# ssl_renew_hook.sh - prove a renewed certificate is the one being served.
#
# Fixes: certbot renews at 02:00 and exits 0, nginx keeps the old certificate
# in memory, and clients see the expiry date two weeks after the renewal was
# reported as successful. The file changed; the process did not.
#
# The hook validates the new certificate (not expired, enough days left, SAN
# contains the domain), records the fingerprint the service is currently
# serving, reloads nginx or a systemd unit, waits, fetches the served
# certificate again and compares it with the new one. Dry run by default.
#
# Usage:
#   ssl_renew_hook.sh --cert /etc/letsencrypt/live/app/fullchain.pem \
#     --domain app.example.com
#   ssl_renew_hook.sh --cert ... --domain app.example.com --apply
#   ssl_renew_hook.sh --cert new.pem --domain app.example.com \
#     --served-cert /tmp/served.pem --reload-cmd /tmp/mock-reload --apply
#
# Certbot deploy hook:
#   --deploy-hook "/usr/local/bin/ssl_renew_hook.sh --cert \
#     /etc/letsencrypt/live/app/fullchain.pem --domain app.example.com --apply"
#
# Exit codes:
#   0  certificate valid (dry run) or served certificate verified (apply)
#   1  invalid certificate, bad SAN, failed reload, or unchanged served cert
#   2  usage error, unreadable input, or a missing tool
#
# Requires openssl 1.1.1+ and GNU date (date -d). nginx or systemctl is
# needed only for a real reload. --served-cert and --reload-cmd exist for
# tests and offline checks; no real service is touched in the fixture tests.
# By s0sta.com

PROG=${0##*/}
cert=""
domain=""
service="nginx"
reload_cmd=""
host=""
port=443
served_cert=""
wait_s=2
min_days=30
apply=0
served_tmp=""
after_tmp=""

usage() {
  cat <<'EOF'
ssl_renew_hook.sh - prove a renewed certificate is the one being served

Usage:
  ssl_renew_hook.sh --cert FILE --domain NAME [options]

Options:
  --cert FILE        new certificate in PEM form (required)
  --domain NAME      name that must appear in the certificate SAN (required)
  --service NAME     systemd unit to reload; default nginx
  --reload-cmd FILE  executable to run instead of nginx/systemctl (tests)
  --host NAME        host to fetch the served cert from; default the domain
  --port N           port for the served cert; default 443
  --served-cert FILE read the served cert from a file instead of the network
  --wait SECS        seconds to wait after reload before fetching; default 2
  --min-days N       require at least N days left; default 30
  --apply            reload the service and verify the served certificate
  -h, --help         show this help and exit 0

Examples:
  ssl_renew_hook.sh --cert /etc/letsencrypt/live/app/fullchain.pem \
    --domain app.example.com
  ssl_renew_hook.sh --cert new.pem --domain app.example.com \
    --served-cert served.pem --reload-cmd ./mock-reload --apply

Exit: 0 valid or verified, 1 invalid or unchanged, 2 usage or unreadable input.
EOF
}

die() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 2
}

# shellcheck disable=SC2329  # called by the EXIT trap
cleanup() {
  if [[ -n $served_tmp ]]; then
    rm -f -- "$served_tmp"
  fi
  if [[ -n $after_tmp ]]; then
    rm -f -- "$after_tmp"
  fi
}
trap cleanup EXIT

fail() {
  printf 'FAIL %s\n' "$1"
  exit 1
}

end_date() {
  openssl x509 -in "$1" -noout -enddate 2>/dev/null | cut -d= -f2
}

days_left() {
  local end epoch
  end=$(end_date "$1") || return 1
  [[ -n $end ]] || return 1
  epoch=$(date -d "$end" +%s 2>/dev/null) || return 1
  printf '%d' $(((epoch - $(date +%s) + 86399) / 86400))
}

fingerprint() {
  openssl x509 -in "$1" -noout -fingerprint -sha256 2>/dev/null | cut -d= -f2
}

short_fp() {
  local fp=$1
  fp=${fp//:/}
  printf '%s' "${fp:0:16}"
}

fetch_served() {
  local dest=$1
  if [[ -n $served_cert ]]; then
    cp -- "$served_cert" "$dest" || return 1
    return 0
  fi
  openssl s_client -connect "$host:$port" -servername "$domain" -showcerts \
    </dev/null 2>/dev/null | openssl x509 -outform PEM >"$dest" || return 1
}

reload_service() {
  if [[ -n $reload_cmd ]]; then
    "$reload_cmd"
    return
  fi
  if [[ $service == nginx ]] && command -v nginx >/dev/null 2>&1; then
    nginx -t && nginx -s reload
    return
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl reload "$service"
    return
  fi
  return 127
}

reload_label() {
  if [[ -n $reload_cmd ]]; then
    printf '%s' "$reload_cmd"
  elif [[ $service == nginx ]] && command -v nginx >/dev/null 2>&1; then
    printf 'nginx -s reload'
  else
    printf 'systemctl reload %s' "$service"
  fi
}

while (($#)); do
  case $1 in
    --cert)
      [[ $# -ge 2 ]] || die "--cert needs a file"
      cert=$2
      shift 2
      ;;
    --domain)
      [[ $# -ge 2 ]] || die "--domain needs a name"
      domain=$2
      shift 2
      ;;
    --service)
      [[ $# -ge 2 ]] || die "--service needs a unit name"
      service=$2
      shift 2
      ;;
    --reload-cmd)
      [[ $# -ge 2 ]] || die "--reload-cmd needs an executable"
      reload_cmd=$2
      shift 2
      ;;
    --host)
      [[ $# -ge 2 ]] || die "--host needs a name"
      host=$2
      shift 2
      ;;
    --port)
      [[ $# -ge 2 ]] || die "--port needs a number"
      port=$2
      shift 2
      ;;
    --served-cert)
      [[ $# -ge 2 ]] || die "--served-cert needs a file"
      served_cert=$2
      shift 2
      ;;
    --wait)
      [[ $# -ge 2 ]] || die "--wait needs a number of seconds"
      wait_s=$2
      shift 2
      ;;
    --min-days)
      [[ $# -ge 2 ]] || die "--min-days needs a number"
      min_days=$2
      shift 2
      ;;
    --apply)
      apply=1
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
      die "unexpected argument: $1 (try --help)"
      ;;
  esac
done

[[ -n $cert ]] || die "--cert is required (try --help)"
[[ -n $domain ]] || die "--domain is required (try --help)"
[[ -r $cert ]] || die "cannot read certificate: $cert"
[[ $wait_s =~ ^[0-9]+$ ]] || die "--wait must be a whole number"
[[ $min_days =~ ^[0-9]+$ ]] || die "--min-days must be a whole number"
[[ $port =~ ^[0-9]+$ ]] || die "--port must be a whole number"
((port >= 1 && port <= 65535)) || die "--port must be 1-65535"
if [[ -n $host ]]; then
  [[ $host != *[[:space:]]* ]] || die "--host must not contain spaces"
else
  host=$domain
fi
if [[ -n $reload_cmd ]]; then
  [[ -x $reload_cmd ]] || die "--reload-cmd is not executable: $reload_cmd"
fi
if [[ -n $served_cert ]]; then
  [[ -r $served_cert ]] || die "cannot read --served-cert: $served_cert"
fi

command -v openssl >/dev/null 2>&1 || die "openssl is not installed"
command -v date >/dev/null 2>&1 || die "date is not installed"

openssl x509 -in "$cert" -noout >/dev/null 2>&1 ||
  fail "not a PEM certificate: $cert"

if ! openssl x509 -in "$cert" -noout -checkend 0 >/dev/null 2>&1; then
  fail "certificate has expired: $cert"
fi
if ((min_days > 0)); then
  if ! openssl x509 -in "$cert" -noout \
      -checkend $((min_days * 86400)) >/dev/null 2>&1; then
    fail "certificate expires in less than --min-days $min_days"
  fi
fi

san_line=$(openssl x509 -in "$cert" -noout -text 2>/dev/null |
  awk '/X509v3 Subject Alternative Name/ { getline; print; exit }') || true
if [[ -z $san_line ]]; then
  fail "certificate has no subjectAltName"
fi
domain_lc=$(printf '%s' "$domain" | tr '[:upper:]' '[:lower:]')
san_ok=0
while IFS= read -r entry; do
  entry=$(printf '%s' "$entry" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  entry_lc=$(printf '%s' "$entry" | tr '[:upper:]' '[:lower:]')
  if [[ $entry_lc == "dns:$domain_lc" ]]; then
    san_ok=1
  fi
done < <(printf '%s\n' "$san_line" | tr ',' '\n')
if ((san_ok == 0)); then
  fail "SAN does not contain DNS:$domain"
fi

new_fp=$(fingerprint "$cert")
[[ -n $new_fp ]] || fail "cannot read the new fingerprint"
exp_days=$(days_left "$cert") || exp_days="?"
exp_end=$(end_date "$cert")
exp_day=$(date -u -d "$exp_end" +%F 2>/dev/null || printf '%s' "$exp_end")

printf 'CERT %s\n' "$cert"
printf 'EXPIRES %s (%sd left)\n' "$exp_day" "$exp_days"
printf 'SAN DNS:%s present\n' "$domain"

served_tmp=$(mktemp "${TMPDIR:-/tmp}/ssl_renew_hook.XXXXXX") ||
  die "mktemp failed"
if ! fetch_served "$served_tmp"; then
  fail "cannot fetch the served certificate from $host:$port"
fi
old_fp=$(fingerprint "$served_tmp")
[[ -n $old_fp ]] || fail "cannot read the served fingerprint"
old_days=$(days_left "$served_tmp") || old_days="?"
old_end=$(end_date "$served_tmp")
old_day=$(date -u -d "$old_end" +%F 2>/dev/null || printf '%s' "$old_end")

printf 'SERVED %s (%s, %sd left)\n' \
  "$(short_fp "$old_fp")" "$old_day" "$old_days"

if [[ $old_fp == "$new_fp" ]]; then
  printf 'OK already serving the new certificate\n'
  exit 0
fi

if ((apply == 0)); then
  printf 'PLAN reload %s, wait %ss, fetch the served cert again\n' \
    "$(reload_label)" "$wait_s"
  printf 'DRY-RUN not reloaded. Add --apply.\n'
  exit 0
fi

printf 'RELOAD %s\n' "$(reload_label)"
if ! reload_service; then
  fail "reload failed: $(reload_label)"
fi
sleep "$wait_s"

after_tmp=$(mktemp "${TMPDIR:-/tmp}/ssl_renew_hook.XXXXXX") ||
  die "mktemp failed"
if ! fetch_served "$after_tmp"; then
  fail "cannot fetch the served certificate after reload"
fi
after_fp=$(fingerprint "$after_tmp")
[[ -n $after_fp ]] || fail "cannot read the served fingerprint after reload"

if [[ $after_fp == "$new_fp" ]]; then
  printf 'OK served certificate is the new one\n'
  exit 0
fi
if [[ $after_fp == "$old_fp" ]]; then
  printf 'FAIL served cert unchanged\n'
  printf 'OLD expires %s, %sd left\n' "$old_day" "$old_days"
  exit 1
fi
printf 'FAIL served certificate is neither old nor new\n'
exit 1
