---
id: p75
title: "5 commands that take servers down"
slug: 5-commands-that-take-servers-down
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, DevOps, BestPractices, CommandLine]
source: "LinkedIn post P75 · Linux series"
linkedin_date: 2027-03-21
design: dontdo
---

# 5 commands that take servers down

Five commands that look harmless and have taken real servers down. Each one has a safer version that costs nothing.

## Quick reference

**1. Don't**

```bash
rm -rf $APP_DIR/
```

If APP_DIR is empty, this becomes `rm -rf /`.

**Do instead**

```bash
rm -rf "${APP_DIR:?}"/
```

`${VAR:?}` stops the command if the variable is empty.

**2. Don't**

```bash
crontab -r
```

One key away from -e. Deletes the whole crontab, no question.

**Do instead**

```bash
crontab -l > ~/crontab.bak
```

Back it up first, then edit with `crontab -e`.

**3. Don't**

```bash
echo '10.0.0.5 db' > /etc/hosts
```

\> replaces the whole file. localhost is gone too.

**Do instead**

```bash
echo '10.0.0.5 db' >> /etc/hosts
```

\>> appends. Better still, copy the file first.

**4. Don't**

```bash
systemctl restart sshd
```

One typo in sshd_config and nobody can log in again.

**Do instead**

```bash
sshd -t && systemctl reload sshd
```

Test the config first. Keep a second session open.

**5. Don't**

```bash
reboot
```

In the wrong terminal tab, that is production.

**Do instead**

```bash
apt install molly-guard
```

Asks for the host name before a `reboot` over SSH.

## Explained

1. `rm -rf $APP_DIR/`
   If APP_DIR is empty or unset, the shell runs `rm -rf /`. Instead: `rm -rf "${APP_DIR:?}"/` — the :? makes the shell stop with an error if the variable is empty.

2. `crontab -r`
   r and e sit right next to each other on the keyboard. -e edits. -r deletes the whole crontab without asking. Instead: `crontab -l > ~/crontab.bak` before you touch it, and keep that habit.

3. `echo '10.0.0.5 db' > /etc/hosts`
   A single > replaces the entire file. Your localhost line is gone, and strange things start to break. Instead: >> appends. And for any system file, cp it to a .bak first.

4. `systemctl restart sshd`
   After editing sshd_config, one typo means the SSH daemon does not come back, and on a remote server that can mean no way in. Instead: `sshd -t` to test the config, then reload, with a second session still open.

5. `reboot`
   Typed into the wrong terminal tab, that is a production outage. Instead: install molly-guard on Debian or Ubuntu. Over SSH, it asks you to type the host name before a `reboot` or shutdown goes through.

> **The pattern behind all five:** the dangerous version is the fast one. The safe version adds one check that takes a second.

Before anything risky, three commands: hostname, whoami, pwd. Where am I, who am I, and where exactly will this run?

## In one line

> **Slow down for one second.** Most outages start with a command that ran too fast.

**Before anything risky**

```bash
hostname; whoami; pwd
```
