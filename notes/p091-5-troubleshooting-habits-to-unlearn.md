---
id: p91
title: "5 troubleshooting habits to unlearn"
slug: 5-troubleshooting-habits-to-unlearn
sections: [it]
topic: "IT operations & incidents"
tags: [Linux, Troubleshooting, SysAdmin, DevOps, IncidentResponse]
source: "LinkedIn post P91 · Linux series"
linkedin_date: 2027-04-27
design: dontdo
---

# 5 troubleshooting habits to unlearn

Most troubleshooting time is not lost on hard problems. It is lost on habits that hide the real cause. Five to unlearn.

## Quick reference

**1. Don't**

```bash
systemctl restart app
```

Restarting first wipes out the evidence.

**Do instead**

```bash
journalctl -u app --since '10 min ago'
```

Read what happened first. Then restart.

**2. Don't**

```bash
tail -f /var/log/app.log
```

After log rotation, -f keeps watching the old file.

**Do instead**

```bash
tail -F /var/log/app.log
```

-F follows the file name, even after rotation.

**3. Don't**

```bash
grep '03:00' app.log
```

App logs often use UTC. You may read the wrong hour.

**Do instead**

```bash
timedatectl
```

Check the server time zone before you compare times.

**4. Don't**

```bash
vi nginx.conf php.ini my.cnf
```

Three changes at once. Which one fixed it, or broke it?

**Do instead**

```bash
git -C /etc commit -am 'one change'
```

One change at a time, with a record of each.

**5. Don't**

```bash
journalctl -u app
```

The app log only shows the app. The cause may be below it.

**Do instead**

```bash
dmesg -T | tail -20
```

Disk errors, OOM kills and hardware faults live here.

## Explained

1. Restarting first
   `systemctl restart app` often makes the symptom go away, and takes the explanation with it. Instead: `journalctl -u app --since '10 min ago'` first. Thirty seconds of reading tells you whether this will happen again tonight.

2. `tail -f` on a log that rotates
   When logrotate renames the file, `tail -f` keeps watching the old one. The screen goes quiet and you think the problem stopped. Instead: `tail -F` follows the file name, and picks up the new file after rotation.

3. Ignoring time zones
   The app logs in UTC, the server shows local time, and the monitoring tool uses a third. You end up comparing events that are hours apart. Instead: check `timedatectl` first, and note which time zone each log uses before you build a timeline.

4. Changing several things at once
   Three config files edited, one restart, and the problem is gone. Which change fixed it? Or which one will break something next week? Instead: one change, one test, and a record of it. With `/etc` in git, every change is one commit.

5. Only reading the app's log
   The application log only knows about the application. A failing disk, an OOM kill or a network driver problem happens below it. Instead: `dmesg -T | tail -20` shows the kernel's side of the story, with readable timestamps.

The first two commands for any failing service: systemctl status app, then `journalctl -xeu` app.

## In one line

> **Slow is smooth. Smooth is fast.** Read first, change one thing, write it down.

**The first two commands**

```bash
systemctl status app; journalctl -xeu app
```
