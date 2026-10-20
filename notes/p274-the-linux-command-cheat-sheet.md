---
id: p274
title: "The Linux command cheat sheet"
slug: the-linux-command-cheat-sheet
sections: [it, devsecops]
topic: "Linux"
tags: [Linux, CommandLine, SysAdmin, DevOps, CheatSheet]
source: "LinkedIn post P274 · Visual series"
linkedin_date: 2028-06-27
design: cheatsheet
---

# The Linux command cheat sheet

Most days on a Linux server need a small, boring set of commands. Not fifty flags you found on a blog, but five per area that you can type without thinking.

## Quick reference

### Files

```bash
ls -lah
cd /var/log
cp -a src/ dst/
mv old.txt new.txt
find / -name '*.log' 2>/dev/null
```

### Processes

```bash
ps aux | grep nginx
top -o %CPU
kill -TERM <pid>
systemctl status nginx
journalctl -u nginx -f
```

### Disk

```bash
df -h
du -sh /var/log/*
lsblk -f
free -h
mount | column -t
```

### Network

```bash
ss -tlnp
ip -br addr
curl -I https://example.com
dig example.com +short
tcpdump -i any port 443
```

## Explained

Files. `ls -lah` gives you the listing you actually want: hidden files, human sizes, permissions. `cp -a` preserves the things you forget: timestamps, symlinks, ownership. find with -name is still the fastest way to answer "where is that log".

Processes. ps aux | grep is crude and works. `top -o %CPU` answers "what is eating the box" without a dashboard. systemctl status and `journalctl -u` are the pair you use on any systemd host, and `kill -TERM` asks politely before -9 ends the argument.

Disk. `df -h` shows the filesystem, `du -sh` shows the folder, and the gap between them is usually a deleted-but-open file. `lsblk -f` shows what is actually mounted where. `free -h` is the first thing to check when a process disappears at night.

Network. `ss -tlnp` shows what is listening, `ip -br addr` is the short address view, `curl -I` proves the service answers, dig answers DNS, and tcpdump is the last resort that settles arguments.

> **The lesson:** a cheat sheet is not a reference. It is the set of commands you can recall under pressure.

## In one line

> **Know the command, skip the search.** Five per area beats fifty you cannot recall.

**A first look**

```bash
uptime; df -h; free -h
```
