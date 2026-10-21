#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# package_integrity.sh - find package files that changed without a deploy.
# Fixes: a binary, config or library modified after its package was installed.
# Read-only: runs rpm -Va or dpkg --verify and reads the result.
#
# Usage:
#   package_integrity.sh [options]
#   package_integrity.sh --verify /tmp/verify.txt --owners /tmp/owners.txt
#
# Options:
#   --verify FILE   captured rpm -Va or dpkg --verify output (default: run it)
#   --tool NAME     rpm, dpkg or auto (default auto)
#   --owners FILE   path-to-package map for fixture runs, "path package"
#   --max N         show at most N changed paths (default 10)
#   -h, --help      show this help and exit 0
#
# Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
# Needs: rpm (RHEL family) or dpkg (Debian family), awk, sort. Linux.
# Cron: 0 7 * * * /usr/local/bin/package_integrity.sh
# By s0sta.com

usage() {
    cat <<'EOF'
package_integrity.sh - find package files that changed without a deploy.

Usage:
  package_integrity.sh [options]
  package_integrity.sh --verify /tmp/verify.txt --owners /tmp/owners.txt

Options:
  --verify FILE   captured rpm -Va or dpkg --verify output (default: run it)
  --tool NAME     rpm, dpkg or auto (default auto)
  --owners FILE   path-to-package map for fixture runs, "path package"
  --max N         show at most N changed paths (default 10)
  -h, --help      show this help and exit 0

Compares the package database with the files on disk, groups the changes by
package and exits 1 when anything differs. Read-only.
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

verify_file=""
owners_file=""
tool=auto
max_show=10

while [ "$#" -gt 0 ]; do
    case "$1" in
        --verify) [ "$#" -ge 2 ] || die "missing value for $1"; verify_file=$2; shift 2 ;;
        --tool)   [ "$#" -ge 2 ] || die "missing value for $1"; tool=$2; shift 2 ;;
        --owners) [ "$#" -ge 2 ] || die "missing value for $1"; owners_file=$2; shift 2 ;;
        --max)    [ "$#" -ge 2 ] || die "missing value for $1"; max_show=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *)        die "unknown option: $1 (try --help)" ;;
    esac
done

is_number "$max_show" || die "not a number: $max_show"
case "$tool" in
    rpm|dpkg|auto) ;;
    *) die "bad --tool, want rpm, dpkg or auto: $tool" ;;
esac

if [ -n "$verify_file" ]; then
    [ -r "$verify_file" ] || die "cannot read verify output: $verify_file"
fi
if [ -n "$owners_file" ]; then
    [ -r "$owners_file" ] || die "cannot read owners map: $owners_file"
fi

if [ "$tool" = auto ]; then
    if command -v rpm >/dev/null 2>&1; then
        tool=rpm
    elif command -v dpkg >/dev/null 2>&1; then
        tool=dpkg
    elif [ -z "$verify_file" ]; then
        die "neither rpm nor dpkg found"
    else
        tool=unknown
    fi
fi

if [ -n "$verify_file" ]; then
    verify_out=$(cat "$verify_file")
else
    if [ "$tool" = rpm ]; then
        verify_out=$(rpm -Va) || die "rpm -Va failed"
    elif [ "$tool" = dpkg ]; then
        verify_out=$(dpkg --verify) || die "dpkg --verify failed"
    else
        die "no package tool available"
    fi
fi

verify_out=$(printf '%s\n' "$verify_out" | sort -u)

attribute() {
    local f pkg
    f=$1
    pkg=""
    if [ -n "$owners_file" ]; then
        pkg=$(awk -v f="$f" '$1 == f { print $2; exit }' "$owners_file" || true)
    elif [ "$tool" = rpm ]; then
        pkg=$(rpm -qf --qf '%{NAME}\n' "$f" 2>/dev/null | sed -n '1p' || true)
    elif [ "$tool" = dpkg ]; then
        pkg=$(dpkg -S "$f" 2>/dev/null | sed -n '1p' | cut -d: -f1 || true)
    fi
    printf '%s\n' "${pkg:-unknown}"
}

files=()
pkgs=()

while IFS= read -r line; do
    [ -n "$line" ] || continue
    path=${line##* }
    case "$path" in
        /*) ;;
        *) continue ;;
    esac
    files+=("$path")
    pkgs+=("$(attribute "$path")")
done <<< "$verify_out"

file_count=${#files[@]}
if [ "$file_count" -gt 0 ]; then
    pkg_count=$(printf '%s\n' "${pkgs[@]}" | sort -u | grep -c . || true)
else
    pkg_count=0
fi

printf 'FINDING files changed: %d, packages: %d\n' "$file_count" "$pkg_count"

if [ "$file_count" -gt 0 ]; then
    top=$(printf '%s\n' "${pkgs[@]}" | sort | uniq -c | sort -k1,1nr -k2,2 | sed -n '1p')
    top=${top#"${top%%[![:space:]]*}"}
    top_count=${top%% *}
    top_pkg=${top#* }
    printf 'ALERT top package: %s (%s of %d)\n' "$top_pkg" "$top_count" "$file_count"

    printf '%s\n' "${pkgs[@]}" | sort | uniq -c | sort -k1,1nr -k2,2 | while IFS=' ' read -r n pkg; do
        printf 'PACKAGE %s %s\n' "$pkg" "$n"
    done

    if [ "$max_show" -gt 0 ]; then
        printf '%s\n' "${files[@]}" | sort -u | while IFS= read -r path; do
            printf 'CHANGED %s\n' "$path"
        done | sed -n "1,${max_show}p"
    fi
fi

if [ "$file_count" -gt 0 ]; then
    exit 1
fi
exit 0
