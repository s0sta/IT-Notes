---
id: p80
title: "9 tar and compression commands"
slug: 9-tar-and-compression-commands
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, Backup, CommandLine, DevOps]
source: "LinkedIn post P80 · Linux series"
linkedin_date: 2027-04-01
design: terminal
---

# 9 tar and compression commands

Every admin uses tar. Most people know one command by heart and search for the rest. Nine that cover nearly every real situation.

## Quick reference

### Pack it

```bash
# c = create, z = gzip, f = the file name
tar -czf site.tar.gz /var/www/site
# leave logs and caches out of the archive
tar -czf site.tar.gz --exclude='*.log' /var/www/site
# zstd: much faster than gzip. -T0 uses every core
tar -cf - /var/www/site | zstd -T0 > site.tar.zst
```

### Look before you unpack

```bash
# list the contents. Note: no leading /
tar -tzf site.tar.gz | head -3
# check the size before you copy it anywhere
ls -lh site.tar.gz
# test that the archive is not corrupt
gzip -t site.tar.gz && echo OK
```

### Unpack it safely

```bash
# -C: extract into a folder, not where you stand
tar -xzf site.tar.gz -C /tmp/restore
# extract one file only
tar -xzf site.tar.gz var/www/site/wp-config.php
# zip files: list first, then unzip -d folder
unzip -l theme.zip
```

## Explained

### Pack it

- `tar -czf site.tar.gz /var/www/site` — c creates an archive, z compresses it with gzip, f names the file. tar removes the leading / so the archive can be extracted anywhere.
- `tar -czf site.tar.gz --exclude='*.log' /var/www/site` — leave logs, caches and build folders out. Smaller archives, faster copies.
- `tar -cf - /var/www/site | zstd -T0 > site.tar.zst` — zstd compresses much faster than gzip at a similar size, and -T0 uses every CPU core. Recent tar versions also support `--zstd` directly.

### Look before you unpack

- `tar -tzf site.tar.gz | head` — list the contents without extracting. You see the folder structure and whether paths start where you expect.
- `ls -lh site.tar.gz` — check the size before you copy a large archive over the network or into a nearly full disk.
- `gzip -t site.tar.gz && echo OK` — test that the compressed file is not corrupt. Better to know now than during a restore.

### Unpack it safely

- `tar -xzf site.tar.gz -C /tmp/restore` — extract into a specific folder. Without -C, everything lands in the directory you are standing in, which may be the live site.
- `tar -xzf site.tar.gz var/www/site/wp-config.php` — restore a single file. Use the path exactly as `tar -t` shows it.
- `unzip -l theme.zip` — zip files work the same way: list first, then `unzip -d` folder to extract somewhere safe.

The habit that matters: list an archive before you trust it, and extract into a temporary folder before you copy anything back.

A backup you have never opened is only a hope.

## In one line

> **List it before you trust it.** A backup you have never opened is only a hope.

**Try it**

```bash
tar -tzf backup.tar.gz | head
```
