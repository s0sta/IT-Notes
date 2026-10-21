---
id: p624
title: "Ports nobody remembers opening"
slug: ports-nobody-remembers-opening
sections: [it, devsecops]
topic: "Shell scripts"
tags: [Bash, Linux, Networking, CyberSecurity, SRE]
source: "LinkedIn post P624 · ShellSec series"
linkedin_date: 2030-09-22
design: code
script: open_ports.sh
---

# Ports nobody remembers opening

A crypto miner ran for eleven days on port 8080. Nobody opened it on purpose; a test harness started on 0.0.0.0 and was never stopped.

## Quick reference

The full script is at the end of this note: `open_ports.sh` (plain Bash and standard Linux tools).

**Run it**

```bash
bash open_ports.sh --ss /tmp/p624/ss.txt --allow /tmp/p624/ok
```

**Example output**

```text
FINDING 1 listener to review
ALERT 8080/tcp python3 on 0.0.0.0
```

## Explained

### What it does

`open_ports.sh` compares every listener in `ss -H -lntup` with an allowlist file. A port that is not listed is UNEXPECTED. A port allowed only on localhost but bound to 0.0.0.0 or [::] is WILDCARD. Each finding names the protocol, port, process and address; nothing is changed.

### What the screen shows

The fourteen lines filter ss output to TCP and UDP, pull the port and address from each line, and compare them with the allowlist. On the fixture: FINDING 1 listener to review and ALERT 8080/tcp python3 on 0.0.0.0.

### How to run it

bash `open_ports.sh --allow /etc/s0sta/allowed_ports`. Pass `--ss capture.txt` for a saved host. Exit 0 is clean, 1 is a finding, 2 is usage or an unreadable file. Run it after every deploy and once a day from cron.

### The fix

Stop and disable a listener that is not needed. Bind a local-only one to 127.0.0.1 behind a reverse proxy. Add the port to the allowlist with the right public or local qualifier.

### Prevention

Keep the allowlist in configuration management and review its diff. A new listener should be a pull request, not a discovery at 3 a.m.

> **The honest caveat:** ss sees the network namespace it runs in, so a container host needs the host namespace and root for process names.

> **The lesson:** a listener is a promise, and if nobody remembers making it, it is a finding.

## In one line

> **Every port is a decision.** A socket nobody wrote down is a socket nobody owns.

**List the ports**

```bash
ss -H -lntup
```

## Script: open_ports.sh

Download: [scripts/open_ports.sh](../scripts/open_ports.sh)

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# open_ports.sh - show the listeners nobody remembers opening.
# Fixes: a listening port missing from the allowlist, and an allowed service
#        bound to 0.0.0.0 when the allowlist says localhost only. Read-only.
#
# Usage:
#   open_ports.sh [options]
#   open_ports.sh --allow /etc/s0sta/allowed_ports
#   open_ports.sh --ss /tmp/ss.txt --allow ./allowed_ports
#
# Options:
#   --allow FILE   allowlist file (default /etc/s0sta/allowed_ports)
#   --ss FILE      captured `ss -H -lntup` output (default: run ss)
#   -h, --help     show this help and exit 0
#
# Allowlist format, one listener per line, PORT/PROTO [public|local]:
#   22/tcp public
#   443/tcp public
#   3306/tcp local
#   "local" is the default: a 0.0.0.0 or [::] bind is then a finding.
#
# Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
# Needs: iproute2 (ss), grep, awk. Linux. Root shows process names.
# Cron: 30 6 * * * /usr/local/bin/open_ports.sh
# By s0sta.com

usage() {
    cat <<'EOF'
open_ports.sh - show the listeners nobody remembers opening.

Usage:
  open_ports.sh [options]
  open_ports.sh --allow /etc/s0sta/allowed_ports
  open_ports.sh --ss /tmp/ss.txt --allow ./allowed_ports

Options:
  --allow FILE   allowlist file (default /etc/s0sta/allowed_ports)
  --ss FILE      captured `ss -H -lntup` output (default: run ss)
  -h, --help     show this help and exit 0

Allowlist format: PORT/PROTO [public|local], one per line.
Exit codes: 0 clean, 1 findings, 2 usage or unreadable input.
EOF
}

die() {
    printf 'ERROR %s\n' "$*" >&2
    exit 2
}

allow_file=/etc/s0sta/allowed_ports
ss_file=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --allow)   [ "$#" -ge 2 ] || die "missing value for $1"; allow_file=$2; shift 2 ;;
        --ss)      [ "$#" -ge 2 ] || die "missing value for $1"; ss_file=$2; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *)         die "unknown option: $1 (try --help)" ;;
    esac
done

[ -r "$allow_file" ] || die "cannot read allowlist: $allow_file"

if [ -n "$ss_file" ]; then
    [ -r "$ss_file" ] || die "cannot read ss output: $ss_file"
    ss_out=$(cat "$ss_file")
else
    command -v ss >/dev/null 2>&1 || die "ss not found; pass --ss FILE on non-Linux hosts"
    ss_out=$(ss -H -lntup) || die "ss failed"
fi

is_wildcard() {
    case "$1" in
        0.0.0.0|::|'*'|0:0:0:0:0:0:0:0) return 0 ;;
        *) return 1 ;;
    esac
}

findings=()

while IFS=$' \t' read -r proto _ _ _ local_addr _ rest; do
    case "$proto" in
        tcp|udp) ;;
        *) continue ;;
    esac
    [ -n "${local_addr:-}" ] || continue

    addr=${local_addr%:*}
    port=${local_addr##*:}
    addr=${addr%%\%*}
    addr=${addr#[}
    addr=${addr%]}
    case "$port" in
        ''|'*'|*[!0-9]*) continue ;;
    esac

    proc="?"
    if [ -n "${rest:-}" ]; then
        proc=$(printf '%s\n' "$rest" | sed -n 's/.*users:(("\([^"]*\)".*/\1/p')
        proc=${proc:-?}
    fi

    key="$port/$proto"
    qual=$(awk -v k="$key" '$1 == k { print ($2 == "" ? "local" : $2); found = 1; exit }
                             END { if (!found) print "absent" }' "$allow_file")

    kind=""
    if [ "$qual" = absent ]; then
        kind=UNEXPECTED
    elif is_wildcard "$addr" && [ "$qual" != public ]; then
        kind=WILDCARD
    fi

    if [ -n "$kind" ]; then
        findings+=("$(printf '%05d\t%s %s %s on %s' "$port" "$kind" "$key" "$proc" "$addr")")
    fi
done <<< "$ss_out"

sorted=""
if [ "${#findings[@]}" -gt 0 ]; then
    sorted=$(printf '%s\n' "${findings[@]}" | sort -u)
fi
count=$(printf '%s\n' "$sorted" | grep -c . || true)

if [ "$count" -eq 1 ]; then
    label=listener
else
    label=listeners
fi
printf 'FINDING %d %s to review\n' "$count" "$label"

if [ "$count" -gt 0 ]; then
    first=$(printf '%s\n' "$sorted" | sed -n '1p')
    IFS=$'\t' read -r _ detail <<< "$first"
    printf 'ALERT %s\n' "${detail#* }"
    printf '%s\n' "$sorted" | while IFS=$'\t' read -r _ detail; do
        printf '%s\n' "$detail"
    done
fi

if [ "$count" -gt 0 ]; then
    exit 1
fi
exit 0
```
