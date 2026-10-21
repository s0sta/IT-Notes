---
id: p708
title: "The evidence command sheet"
slug: the-evidence-command-sheet
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, DFIR, Linux, CyberSecurity, CommandLine]
source: "LinkedIn post P708 · IR series"
linkedin_date: 2031-04-06
design: cheatsheet
---

# The evidence command sheet

Four blocks of commands for the hour when the evidence still exists: hash it, copy it, and describe what was running and connected.

## Quick reference

### Hash

```bash
sha256sum auth.log
sha256sum -c manifest.sha256
find . -type f -exec sha256sum {} +
sha256sum auth.log > auth.log.sha256
sha256sum /dev/sda | tee disk.sha256
```

### Copy

```bash
cp -a /var/log/auth.log /evidence/
cp --preserve=all auth.log evidence/
rsync -aHAX /var/log/ /evidence/logs/
tar --acls --xattrs -czf logs.tgz logs/
dd if=/dev/sda of=/evidence/sda.img bs=1M
```

### Process

```bash
ps -eo pid,ppid,user,args
ps -eo pid,rss,comm --sort=-rss
ls -l /proc/412/cwd
lsof -p 412
cat /proc/412/status
```

### Network

```bash
ss -tanp
ss -tulpn
ip neigh show
conntrack -L
tcpdump -i any -w capture.pcap
```

## Explained

### Hash

sha256sum prints a digest for one file, and the -c form checks a saved list. The find one-liner hashes a whole tree, while a redirect keeps the digest beside the name it belongs to. Hash the copy and compare it with the source, or hash once and never let the file move.

### Copy

Copy with metadata: `cp -a` keeps times and modes, `--preserve=all` adds the rest, `rsync -aHAX` keeps ACLs and extended attributes, and dd takes a block-device image. tar with `--acls` and `--xattrs` packs a directory without dropping what a plain copy drops.

### Process

ps with an explicit field list is the only version you can diff later. The sort by resident memory names the biggest process, the cwd link shows where it was started, lsof shows what it held open, and `/proc/PID/status` carries the credential and namespace facts.

### Network

`ss -tanp` lists sockets with the owning process, and -tulpn adds the listeners. ip neigh shows the layer-two neighbours, conntrack -L the flows, and tcpdump writes a capture you can hash like any other file.

> **The honest caveat:** a command that prints a secret into a terminal has copied it into your scrollback; redirect to a file with mode 600.

> **The lesson:** hash what you copy, then copy the hash.

## In one line

> **Hash what you copy, then copy the hash.** The digest belongs beside the file, not in a chat message.

**Seal the log**

```bash
sha256sum auth.log > auth.log.sha256
```
