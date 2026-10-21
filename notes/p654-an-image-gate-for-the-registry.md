---
id: p654
title: "An image gate for the registry"
slug: an-image-gate-for-the-registry
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, DevSecOps, Containers, CyberSecurity, CICD]
source: "LinkedIn post P654 · ShellSec series"
linkedin_date: 2030-12-01
design: code
script: image_scan_gate.sh
---

# An image gate for the registry

The registry gate is green because it scans nothing. trivy is not installed, the step is optional, and a CRITICAL base image ships on a Friday.

## Quick reference

The full script is at the end of this note: `image_scan_gate.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
IMAGE_ALLOWLIST=/tmp/s0f/allow-none.txt bash image_scan_gate.sh one:1.4
```

**Example output**

```text
FINDING 1 HIGH/CRITICAL
CRITICAL CVE-2024-21626 runc
```

## Explained

### What it does

`image_scan_gate.sh` takes images from arguments or a file, runs trivy, and keeps every HIGH or CRITICAL vulnerability. Each CVE is checked against an allowlist of IDs, where a comment can carry the owner and expiry. Anything left prints severity, CVE, package and image, then exits 1. When trivy is missing it prints SKIP and exits 2, because a gate that cannot scan must not pass.

### What the screen shows

The fourteen lines check for trivy, scan, select HIGH and CRITICAL with jq, filter the allowlist and report. On the dirty fixture: FINDING 1 HIGH/CRITICAL and CRITICAL CVE-2024-21626 runc. The full script adds the image.

### How to run it

IMAGE_ALLOWLIST=`trivy-allowlist.txt image_scan_gate.sh -f images.txt` in CI, after build and before deploy. Exit 0 is clean or fully allowlisted, 1 is a finding, 2 is a missing tool, a bad image list or invalid JSON.

### The fix

Rebuild on a patched base, or pin the fixed package version. If it does not apply, add the ID with an owner and an expiry date for the next review.

### Prevention

Run it on every tag, not only on release. A weekly scan of what is deployed catches the CVE published after the build.

> **The honest caveat:** a trivy JSON schema change breaks the parse, so pin the version.

> **The lesson:** an allowlist without an owner is a permanent exception.

## In one line

> **A gate that cannot fail is not a gate.** A gate that cannot scan must not report green.

**Fail closed**

```bash
trivy image -s HIGH,CRITICAL nginx
```

## Script: image_scan_gate.sh

Download: [scripts/image_scan_gate.sh](../scripts/image_scan_gate.sh)

```bash
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
```
