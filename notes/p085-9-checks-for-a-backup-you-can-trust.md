---
id: p85
title: "9 checks for a backup you can trust"
slug: 9-checks-for-a-backup-you-can-trust
sections: [it]
topic: "Backup & recovery"
tags: [Backup, Linux, DataProtection, SysAdmin, DisasterRecovery]
source: "LinkedIn post P85 · Linux series"
linkedin_date: 2027-04-13
design: checklist
---

# 9 checks for a backup you can trust

Almost every company has backups. Far fewer have backups they have actually restored. Nine checks for a backup you can trust.

## Quick reference

### The copies

- **3 copies, 2 media, 1 offsite** — the 3-2-1 rule
- **One copy off the server** — `rsync -a /backups/ offsite:/b/`
- **Encrypted at rest** — restic and borg encrypt

### The process

- **Runs on a schedule** — `systemctl list-timers`
- **Alerts when it fails** — on any non-zero exit code
- **Retention is set** — keep 7 daily, 4 weekly

### The proof

```bash
# A restore was tested
tar -xzf db.tar.gz -C /tmp/r
# Databases dumped properly
mysqldump --single-transaction
# Config backed up too
/etc, crontabs, certificates
```

## Explained

### The copies

- **The 3-2-1 rule** — three copies of the data, on two different types of storage, with one copy offsite. A backup on the same disk as the data is not a backup.
- **One copy off the server** — `rsync -a /backups/ offsite:/b/` or a tool like restic or borg to another location. If the server is lost, encrypted by ransomware or deleted, the backup must survive it.
- **Encrypted at rest** — an offsite backup is a full copy of your data somewhere else. restic and borg encrypt by default. Keep the keys somewhere that is not the server itself.

### The process

- **Runs on a schedule** — `systemctl list-timers` or `crontab -l` shows it is really scheduled, and when it last ran.
- **Alerts when it fails** — a backup job that exits with an error and tells nobody is the most common silent failure. Alert on any non-zero exit code, and on a job that did not run at all.
- **Retention is set** — for example 7 daily, 4 weekly and 12 monthly. Without retention, the disk fills up and the newest backups fail first.

### The proof

- **A restore was tested** — extract to a temporary folder like `/tmp/r` and check the files open. Do it monthly, not on the day you need it.
- **Databases dumped properly** — copying the files of a running database can give a broken backup. `mysqldump --single-transaction` or pg_dump give a consistent one.
- **Config backed up too** — `/etc, crontabs, certificates` and keys. Rebuilding a server from memory takes far longer than restoring its config.

## In one line

> **A backup is only a restore you tested.** Test one restore every month. Put it in the calendar.

**Check the last run**

```bash
journalctl -u backup.service -n 20
```
