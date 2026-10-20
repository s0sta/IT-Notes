---
id: p92
title: "Quiz: 3 Linux questions most admins get wrong"
slug: quiz-3-linux-questions-most-admins-get-wrong
sections: [it]
topic: "Linux"
tags: [Linux, SysAdmin, ITCareer, DevOps, CommandLine]
source: "LinkedIn post P92 · Linux + IT series"
linkedin_date: 2027-04-29
design: quiz
---

# Quiz: 3 Linux questions most admins get wrong

Three Linux questions that catch out experienced admins. Answer each one before you read the explanation.

## Quick reference

**Q1. You delete a 10 GB log file, but `df -h` still shows the same usage. Why?**

- a) The filesystem needs a reboot to update
- b) A process still has the file open
- c) Linux keeps deleted files in a trash folder

> **Answer:** b) A process still has the file open. The space is freed only when the last process closes the file. Find it with `lsof +L1`, then restart that process.

**Q2. A 4-core server shows a load average of 4.00. What does that mean?**

- a) It is overloaded at 400%
- b) It is about fully busy, not yet overloaded
- c) Four users are logged in

> **Answer:** b) It is about fully busy, not yet overloaded. Load counts tasks running or waiting. On 4 cores, 4.00 means every core is busy. Above that, work starts to queue.

**Q3. Which file decides whether `/etc/hosts` is checked before DNS?**

- a) `/etc/resolv.conf`
- b) `/etc/nsswitch.conf`
- c) `/etc/hostname`

> **Answer:** b) `/etc/nsswitch.conf`. The hosts: line in `nsswitch.conf` sets the order, usually files then dns. `resolv.conf` only lists the DNS servers.

## Explained

1. You delete a 10 GB log file, but `df -h` still shows the same disk usage. Why?

> **Answer:** a process still has the file open. Deleting a file removes its name, but the data stays on disk until the last process holding it closes the file. `lsof +L1` lists these deleted-but-open files. Restart the process and the space comes back. Next time, empty the file with `truncate -s 0` instead of deleting it.

2. A 4-core server shows a load average of 4.00. What does that mean?

> **Answer:** it is roughly fully busy, but not overloaded. The load average counts tasks that are running or waiting to run, including tasks waiting on disk I/O. On 4 cores, 4.00 means every core has work. A load of 8 on the same machine means tasks are queuing. The number only means something next to the core count, which nproc shows.

3. Which file decides whether `/etc/hosts` is checked before DNS?

> **Answer:** `/etc/nsswitch.conf`. The hosts: line sets the lookup order, usually files dns, meaning the hosts file first and DNS second. `/etc/resolv.conf` only says which DNS servers to ask. This is why an old entry in `/etc/hosts` can override a DNS change and make one server see a different site than everyone else.

None of these are rare situations. All three show up in real tickets every month.

## In one line

> **Fundamentals never expire.** Tools change every year. These answers do not.

**Try the first one**

```bash
lsof +L1
```
