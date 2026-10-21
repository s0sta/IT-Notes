#!/usr/bin/env bash
set -euo pipefail
# image_scan_gate.sh - fail a build on HIGH or CRITICAL image CVEs.
#
# Fixes: the registry gate is green because it scans nothing. This gate runs
# trivy on every image, parses the JSON, and fails unless the CVE is in an
# allowlist where every exception can name an owner and an expiry.
#
# Usage:
#   ./image_scan_gate.sh -f images.txt -a trivy-allowlist.txt
#   ./image_scan_gate.sh ghcr.io/s0sta/api:1.4
#
# CI (before deploy):
#   image_scan_gate.sh -f images.txt -a .github/trivy-allowlist.txt
#
# Weekly drift scan (Monday, 06:00):
#   0 6 * * 1 root /usr/local/sbin/image_scan_gate.sh -f /etc/s0sta/images.txt -a /etc/s0sta/allow.txt
#
# Exit: 0 clean or every finding allowlisted, 1 HIGH/CRITICAL outside the
# allowlist, 2 usage, missing tool, bad JSON or a failed scan.
# trivy and jq are required. Without trivy the gate fails closed with a SKIP
# line rather than passing a build it could not scan. IMAGE_ALLOWLIST is the
# default allowlist; -a overrides it. Allowlist format, one ID per line,
# anything after # is a comment:
#   CVE-2024-21626  # owner: @platform, expires: 2026-12-31
#
# By s0sta.com

IFS=$'\n\t'

ALLOW_FILE=${IMAGE_ALLOWLIST:-}
ALLOW=""
IMAGES=()

usage() {
  cat <<'EOF'
Usage: image_scan_gate.sh [options] [IMAGE...]

Scan images with trivy and fail on HIGH or CRITICAL CVEs.

Options:
  -f, --file FILE       read image references from FILE, one per line
  -a, --allowlist FILE  accepted CVE IDs, one per line; # starts a comment
  -h, --help            show this help and exit

IMAGE_ALLOWLIST names the default allowlist; -a overrides it.
Exit: 0 clean or every finding allowlisted, 1 finding, 2 usage or tool error.
By s0sta.com
EOF
}

die() {
  printf 'ERROR %s\n' "$1" >&2
  exit 2
}

is_allowed() {
  [ -n "$ALLOW" ] || return 1
  printf '%s\n' "$ALLOW" | grep -Fxq -- "$1"
}

while [ "$#" -gt 0 ]; do
  case $1 in
    -h|--help)
      usage
      exit 0
      ;;
    -f|--file)
      [ "$#" -ge 2 ] || die "$1 needs a file"
      [ -r "$2" ] || die "cannot read image list: $2"
      while IFS= read -r line; do
        line=${line%%#*}
        line=$(printf '%s' "$line" | tr -d '[:space:]')
        if [ -n "$line" ]; then
          IMAGES+=("$line")
        fi
      done < "$2"
      shift 2
      ;;
    -a|--allowlist)
      [ "$#" -ge 2 ] || die "$1 needs a file"
      [ -r "$2" ] || die "cannot read allowlist: $2"
      ALLOW_FILE=$2
      shift 2
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        IMAGES+=("$1")
        shift
      done
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      IMAGES+=("$1")
      shift
      ;;
  esac
done

if [ "${#IMAGES[@]}" -eq 0 ]; then
  usage >&2
  die "no images given: pass IMAGE or -f FILE"
fi

if [ -n "$ALLOW_FILE" ]; then
  ALLOW=$(awk '{ sub(/#.*/, ""); if (NF > 0) print $1 }' "$ALLOW_FILE")
fi

if ! command -v trivy >/dev/null 2>&1; then
  printf 'SKIP trivy not installed: cannot scan %d images\n' "${#IMAGES[@]}"
  printf 'Install trivy, or run this gate in the image-scan job.\n' >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  die "jq not installed: cannot parse trivy JSON"
fi

report=""
n=0

for img in "${IMAGES[@]}"; do
  if ! json=$(trivy image --format json --quiet "$img" 2>/dev/null); then
    die "trivy failed for $img"
  fi
  if ! printf '%s' "$json" | jq -e . >/dev/null 2>&1; then
    die "trivy returned invalid JSON for $img"
  fi
  hits=$(printf '%s' "$json" | jq -r '
    .Results[]?.Vulnerabilities[]?
    | select(.Severity == "HIGH" or .Severity == "CRITICAL")
    | [.Severity, .VulnerabilityID, .PkgName] | @tsv
  ')
  if [ -z "$hits" ]; then
    continue
  fi
  while IFS=$'\t' read -r sev cve pkg; do
    [ -n "$cve" ] || continue
    if is_allowed "$cve"; then
      continue
    fi
    report="${report}${sev} ${cve} ${pkg} ${img}"$'\n'
    n=$((n + 1))
  done <<< "$hits"
done

if [ "$n" -gt 0 ]; then
  printf 'FINDING %d HIGH/CRITICAL not allowlisted\n' "$n"
  printf '%s' "$report"
  exit 1
fi

printf 'OK no HIGH/CRITICAL outside the allowlist in %d images\n' "${#IMAGES[@]}"
exit 0
