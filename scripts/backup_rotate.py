#!/usr/bin/env python3
"""backup_rotate.py - timestamped backups that clean up after themselves.

Creates a compressed tar.gz of a source folder into a backup folder, named
with the date and time, then deletes the oldest backups so only the newest N
remain. Standard library only, so it runs anywhere Python does.

Usage:
    python3 backup_rotate.py /var/www /backups
    python3 backup_rotate.py /etc /backups --keep 14 --prefix etc

Cron (daily at 02:00):
    0 2 * * * /usr/bin/python3 /opt/scripts/backup_rotate.py /var/www /backups --keep 7

By s0sta.com
"""
import argparse
import datetime as dt
import sys
import tarfile
from pathlib import Path


def make_backup(src, dest_dir, prefix):
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = dest_dir / f"{prefix}-{stamp}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        tar.add(src, arcname=Path(src).name)
    return out


def rotate(dest_dir, prefix, keep):
    backups = sorted(dest_dir.glob(f"{prefix}-*.tar.gz"))
    removed = []
    while len(backups) > keep:
        old = backups.pop(0)
        old.unlink()
        removed.append(old.name)
    return removed


def main():
    ap = argparse.ArgumentParser(description="Create and rotate tar.gz backups.")
    ap.add_argument("source", help="folder to back up")
    ap.add_argument("dest", help="folder to store backups in")
    ap.add_argument("--keep", type=int, default=7, help="how many backups to keep")
    ap.add_argument("--prefix", help="name prefix, default = source folder name")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        sys.exit(f"source not found: {src}")
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or src.name

    out = make_backup(str(src), dest, prefix)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"[OK] created {out.name} ({size_mb:.1f} MB)")

    removed = rotate(dest, prefix, args.keep)
    for name in removed:
        print(f"[--] removed old backup {name}")
    print(f"[OK] keeping {args.keep} most recent backups")


if __name__ == "__main__":
    main()
