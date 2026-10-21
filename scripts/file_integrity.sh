#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'
#
# file_integrity.sh - create or check a SHA-256 baseline of a directory tree.
#
# Fixes: files that changed under you. --init writes a plain-text baseline
# (one "hash  relative/path" line per regular file); --check re-hashes the
# tree, then reports CHANGED, ADDED and REMOVED files and exits 1. The
# baseline file itself must live outside the tree it describes.
#
# Usage:
#   file_integrity.sh --init  --baseline /var/lib/s0sta/app.sha /srv/app
#   file_integrity.sh --check --baseline /var/lib/s0sta/app.sha /srv/app
#   file_integrity.sh -c -b /var/lib/s0sta/app.sha /srv/app
#   file_integrity.sh --help
#
# Cron (daily, 02:40; exit 1 means the tree changed):
#   40 2 * * * /usr/local/sbin/file_integrity.sh -c \
#     -b /var/lib/s0sta/app.sha /srv/app >>/var/log/s0sta/integrity.log 2>&1
#
# Exit: 0 clean or baseline written, 1 changes found, 2 usage or unreadable
#       input.
# Needs: sha256sum, or shasum -a 256 on macOS/BSD.
# Read-only on --check: only the baseline is read. --init writes one file.
# By s0sta.com
#
usage() {
    cat <<'EOF'
file_integrity.sh - create or check a SHA-256 baseline of a directory tree.

Usage:
  file_integrity.sh --init  --baseline FILE DIR
  file_integrity.sh --check --baseline FILE DIR
  file_integrity.sh --help

  -i, --init         write a new baseline from DIR
  -c, --check        compare DIR with the baseline (default mode)
  -b, --baseline F   baseline file, kept outside DIR
  -h, --help         show this help and exit 0

Exit: 0 clean or baseline written, 1 changes found, 2 usage or unreadable
input. Files are compared by SHA-256; symlinks and special files are skipped.
EOF
}

die() {
    printf 'file_integrity: %s\n' "$1" >&2
    exit 2
}

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" 2>/dev/null | cut -d' ' -f1
    else
        shasum -a 256 "$1" 2>/dev/null | cut -d' ' -f1
    fi
}

MODE=check
BASE=
DIR=
while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        -i|--init) MODE=init; shift ;;
        -c|--check) MODE=check; shift ;;
        -b|--baseline)
            [ "$#" -ge 2 ] || die "--baseline needs a path"
            BASE=$2; shift 2 ;;
        -*) die "unknown argument: $1" ;;
        *)
            [ -z "$DIR" ] || die "only one tree may be given"
            DIR=$1; shift ;;
    esac
done

[ -n "$BASE" ] || die "missing --baseline"
[ -n "$DIR" ] || die "missing DIR"
[ -d "$DIR" ] || die "not a directory: $DIR"
[ -r "$DIR" ] || die "cannot read: $DIR"
if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
    die "need sha256sum or shasum"
fi

BASEDIR=$(cd "$(dirname "$BASE")" 2>/dev/null && pwd) || die "no such directory: $BASE"
BASE_ABS="$BASEDIR/$(basename "$BASE")"
DIR_ABS=$(cd "$DIR" && pwd)
case "$BASE_ABS" in
    "$DIR_ABS"/*) die "baseline must live outside the tree: $BASE_ABS" ;;
esac

if [ "$MODE" = init ]; then
    TMPBASE=$(mktemp "${TMPDIR:-/tmp}/file_integrity.XXXXXX")
    trap 'rm -f "$TMPBASE"' EXIT
    COUNT=0
    while IFS= read -r -d '' path; do
        rel=${path#./}
        hash=$(hash_file "$DIR/$path") || hash=
        [ -n "$hash" ] || die "cannot hash: $path"
        printf '%s  %s\n' "$hash" "$rel" >>"$TMPBASE"
        COUNT=$((COUNT + 1))
    done < <(cd "$DIR" && find . -type f -print0)
    LC_ALL=C sort -k2 -o "$TMPBASE" "$TMPBASE"
    mv "$TMPBASE" "$BASE_ABS"
    printf 'BASELINE %d files written to %s\n' "$COUNT" "$BASE_ABS"
    exit 0
fi

[ -f "$BASE_ABS" ] || die "baseline not found: $BASE_ABS"
[ -r "$BASE_ABS" ] || die "cannot read baseline: $BASE_ABS"

TMP=$(mktemp -d "${TMPDIR:-/tmp}/file_integrity.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
: >"$TMP/changed"
: >"$TMP/added"
: >"$TMP/removed"
: >"$TMP/paths"

# Pass 1: everything in the baseline must still exist and match.
while IFS= read -r line || [ -n "$line" ]; do
    [ -n "$line" ] || continue
    hash=${line%%  *}
    rel=${line#*  }
    if [ "$hash" = "$line" ] || [ -z "$rel" ]; then
        die "malformed baseline line: $line"
    fi
    printf '%s\n' "$rel" >>"$TMP/paths"
    target="$DIR_ABS/$rel"
    if [ ! -e "$target" ]; then
        printf '%s\n' "$rel" >>"$TMP/removed"
        continue
    fi
    live=$(hash_file "$target") || live=
    if [ -z "$live" ]; then
        die "cannot hash: $target"
    fi
    if [ "$live" != "$hash" ]; then
        printf '%s\n' "$rel" >>"$TMP/changed"
    fi
done <"$BASE_ABS"

# Pass 2: everything in the tree must be in the baseline.
while IFS= read -r -d '' path; do
    rel=${path#./}
    if ! grep -qxF -e "$rel" "$TMP/paths"; then
        printf '%s\n' "$rel" >>"$TMP/added"
    fi
done < <(cd "$DIR_ABS" && find . -type f -print0)

CHANGED=$(wc -l <"$TMP/changed" || true)
ADDED=$(wc -l <"$TMP/added" || true)
REMOVED=$(wc -l <"$TMP/removed" || true)
TOTAL=$((CHANGED + ADDED + REMOVED))

if [ "$TOTAL" -eq 0 ]; then
    printf 'OK no changes in %s\n' "$DIR_ABS"
    exit 0
fi

if [ "$TOTAL" -eq 1 ]; then
    printf 'FINDING 1 change\n'
else
    printf 'FINDING %d changes\n' "$TOTAL"
fi
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    printf 'CHANGED %s\n' "$rel"
done < <(LC_ALL=C sort "$TMP/changed")
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    printf 'ADDED %s\n' "$rel"
done < <(LC_ALL=C sort "$TMP/added")
while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    printf 'REMOVED %s\n' "$rel"
done < <(LC_ALL=C sort "$TMP/removed")

exit 1
