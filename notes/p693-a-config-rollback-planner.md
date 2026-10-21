---
id: p693
title: "A config rollback planner"
slug: a-config-rollback-planner
sections: [it, devsecops]
topic: "Python scripts"
tags: [Python, IncidentResponse, Linux, SRE, ConfigurationManagement]
source: "LinkedIn post P693 · IR series"
linkedin_date: 2031-03-02
design: code
script: config_rollback.py
---

# A config rollback planner

The 01:55 deploy changed one line in `nginx.conf` and the edge started returning 502s. Git has the change; the last-known-good directory has the version that worked. The hard part is proving which files differ.

## Quick reference

The full script is at the end of this note: `config_rollback.py` (standard library only, no `pip install`).

**Run it**

```bash
python3 config_rollback.py /tmp/c /tmp/l -r /etc
```

**Example output**

```text
ROLLBACK web-01: cp -p /tmp/l/web-01/nginx.conf /etc/nginx.conf
FAIL drift on web-01: 1 file
```

## Explained

### What it does

`config_rollback.py` walks a current tree and a last-known-good tree, host by host, and hashes every regular file with SHA-256. Equal files are OK, changed files are DRIFT, files only in the LKG are MISSING, and files only in current are EXTRA. For every drifted or missing file it prints the exact `cp -p` command, and exits 1 on any difference.

### What the screen shows

The fourteen lines hash both sides, collect the drift, then print the command and summary. The dirty fixture ends on ROLLBACK web-01: `cp -p /tmp/l/web-01/nginx.conf /etc/nginx.conf` and FAIL drift on web-01: 1 file.

### How to run it

`python3 config_rollback.py current/ lkg/ --target-root /etc`. Add `--host web-01` to plan one host. Exit 0 is a clean tree, 1 is drift, 2 is bad layout.

### The fix

Copy the named files, then reload the service that owns them. A config file on disk is not a config in memory: nginx, systemd and the app all cache. Compare the running config too, with `nginx -T` or the app's endpoint.

### Prevention

Snapshot the LKG tree before every deploy, outside the release path. A last-known-good directory inside the release directory is deleted by the next release.

> **The honest caveat:** SHA-256 proves the bytes, not that the file parses. Run `nginx -t` after the copy.

> **The lesson:** rollback is a file-level plan, not a feeling.

## In one line

> **The old file is the rollback.** A hash match is the only rollback you can prove.

**Plan first**

```bash
python3 config_rollback.py cur lkg
```

## Script: config_rollback.py

Download: [scripts/config_rollback.py](../scripts/config_rollback.py)

```python
#!/usr/bin/env python3
"""config_rollback.py - print the per-host rollback plan for drifted config.

Compares a current config tree with a last-known-good (LKG) tree, host by
host, using SHA-256. Equal files are OK; a file that changed is DRIFT; a file
that exists only in the LKG is MISSING; a file that exists only in current is
EXTRA. Drift, missing and extra all make the run exit 1.

Both trees must use the same shape: <root>/<host>/<relative path>, so
current/web-01/etc/nginx/nginx.conf is compared with
lkg/web-01/etc/nginx/nginx.conf. The plan prints the exact cp -p command for
every drifted or missing file, with --target-root as the live root.

The comparison is read-only: it hashes files and prints commands. It does not
copy, reload or restart anything. A copied file is not a loaded config, so
reload the service after the plan and run its own config test.

Usage:
    python3 config_rollback.py current/ lkg/
    python3 config_rollback.py current/ lkg/ --target-root /srv/live
    python3 config_rollback.py current/ lkg/ --host web-01
    python3 config_rollback.py --help

Cron (hourly drift report, exit 1 on any drift):
    0 * * * * python3 /opt/s0sta/config_rollback.py /srv/current \
      /srv/lkg >> /var/log/ir/config_drift.log 2>&1

CI (before a deploy, prove the tree still matches the last known good):
    python3 config_rollback.py current/ lkg/ || exit 1

Exit codes: 0 every file matches the last known good, 1 at least one file
drifted, is missing or is extra, 2 usage error, unreadable tree, bad layout or
unreadable file.

Read-only: both trees are opened for reading only and nothing is written.
Symlinks are skipped, not followed. The SHA-256 proves the bytes, not that the
config parses; run nginx -t (or the application's own check) after the copy.

By s0sta.com
"""
import argparse
import hashlib
import os
import shlex
import sys


def die(message):
    print("ERROR " + message, file=sys.stderr)
    sys.exit(2)


def digest(path):
    value = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                value.update(chunk)
    except OSError as exc:
        die("%s: %s" % (path, exc.strerror or exc))
    return value.hexdigest()


def walk(root, label):
    if not os.path.isdir(root):
        die("%s is not a directory: %s" % (label, root))
    files = {}
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs
                         if not os.path.islink(os.path.join(base, d)))
        for name in sorted(names):
            path = os.path.join(base, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            files[os.path.relpath(path, root)] = path
    if not files:
        die("%s has no regular files: %s" % (label, root))
    return files


def host_names(root, label):
    names = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if os.path.isdir(path) and not os.path.islink(path):
            names.append(name)
        elif os.path.isfile(path):
            die("%s: top-level file %s; expected <root>/<host>/..."
                % (label, name))
    if not names:
        die("%s: expected <root>/<host>/...; no host directories in %s"
            % (label, root))
    return names


def main():
    parser = argparse.ArgumentParser(
        description="Compare current config with a last-known-good tree and "
                    "print the exact per-host rollback commands.")
    parser.add_argument("current", help="current config tree (<root>/<host>/...)")
    parser.add_argument("lkg", help="last-known-good tree, same shape")
    parser.add_argument("--host", action="append", default=None,
                        help="only this host; repeat for more than one")
    parser.add_argument("-r", "--target-root", default="/",
                        help="live root the relative paths are restored under "
                             "(default /)")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    args = parser.parse_args()

    current = walk(args.current, "current")
    lkg = walk(args.lkg, "lkg")
    target_root = os.path.abspath(args.target_root)

    hosts = sorted(set(host_names(args.current, "current"))
                   | set(host_names(args.lkg, "lkg")))
    if args.host:
        missing = [h for h in args.host if h not in hosts]
        if missing:
            die("unknown host%s: %s"
                % ("" if len(missing) == 1 else "s", ", ".join(missing)))
        hosts = [h for h in hosts if h in args.host]

    findings = 0
    plans = []
    summary = []
    for host in hosts:
        prefix = host + os.sep
        left = {rel: path for rel, path in current.items()
                if rel.startswith(prefix)}
        right = {rel: path for rel, path in lkg.items()
                 if rel.startswith(prefix)}
        rows = []
        drift = 0
        for rel in sorted(set(left) | set(right)):
            short = rel[len(prefix):]
            if rel in left and rel in right:
                first, second = digest(left[rel]), digest(right[rel])
                if first == second:
                    rows.append(("OK", short, first, second))
                else:
                    drift += 1
                    rows.append(("DRIFT", short, first, second))
            elif rel in right:
                drift += 1
                rows.append(("MISSING", short, "-", digest(right[rel])))
            else:
                drift += 1
                rows.append(("EXTRA", short, digest(left[rel]), "-"))

        if drift == 0:
            print("HOST %s %d file%s match" %
                  (host, len(rows), "" if len(rows) == 1 else "s"))
        else:
            print("HOST %s %d file%s, %d difference%s"
                  % (host, len(rows), "" if len(rows) == 1 else "s",
                     drift, "" if drift == 1 else "s"))
        for kind, short, first, second in rows:
            if kind == "OK":
                print("OK %s" % short)
            elif kind == "DRIFT":
                print("DRIFT %s lkg=%s current=%s" % (short, second[:8], first[:8]))
            elif kind == "MISSING":
                print("MISSING %s (only in the last known good)" % short)
            else:
                print("EXTRA %s (not in the last known good, review it)" % short)
            if kind in ("DRIFT", "MISSING"):
                source = right[host + os.sep + short]
                target = os.path.join(target_root, short)
                plans.append("ROLLBACK %s: cp -p %s %s"
                             % (host, shlex.quote(source), shlex.quote(target)))
        findings += drift
        summary.append((host, len(rows), drift))

    total_files = sum(item[1] for item in summary)
    print("CHECK %d host%s, %d file%s, %d difference%s"
          % (len(summary), "" if len(summary) == 1 else "s",
             total_files, "" if total_files == 1 else "s",
             findings, "" if findings == 1 else "s"))
    if findings == 0:
        print("OK every file matches the last known good")
        return 0

    print("PLAN %d rollback command%s" % (len(plans),
                                          "" if len(plans) == 1 else "s"))
    for plan in plans:
        print(plan)
    bad_hosts = [host for host, _, drift in summary if drift]
    print("FAIL drift on %s: %d file%s"
          % (", ".join(bad_hosts), findings,
             "" if findings == 1 else "s"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
