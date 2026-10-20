---
id: p114
title: "Quiz: 3 Active Directory questions"
slug: quiz-3-active-directory-questions
sections: [it]
topic: "Windows & Active Directory"
tags: [ActiveDirectory, WindowsServer, SysAdmin, ITSupport, ITCareer]
source: "LinkedIn post P114 · Linux + IT series"
linkedin_date: 2027-06-20
design: quiz
---

# Quiz: 3 Active Directory questions

Three Active Directory questions that come up in real work all the time. Try them before you read the answers.

## Quick reference

**Q1. Which FSMO role is the main time source for the whole domain?**

- a) RID Master
- b) PDC Emulator
- c) Schema Master

> **Answer:** b) PDC Emulator. The PDC Emulator in the forest root domain syncs with a reliable outside source. Every other machine follows it.

**Q2. A user was just added to a group but still cannot open the share. Fastest fix?**

- a) Restart the file server
- b) Log off and log on again
- c) Run gpupdate /force

> **Answer:** b) Log off and log on again. Group membership is in the Kerberos ticket from logon. A new logon, or klist purge, gets a fresh ticket.

**Q3. Which command shows a summary of AD replication health?**

- a) `repadmin /replsummary`
- b) ipconfig /registerdns
- c) netdom resetpwd

> **Answer:** a) `repadmin /replsummary`. `repadmin /replsummary` lists failures and the longest replication delay for each domain controller.

## Explained

1. Which FSMO role is the main time source for the whole domain?

> **Answer:** the PDC Emulator. In a domain, member computers sync their clocks with a domain controller, domain controllers sync with the PDC Emulator, and the PDC Emulator of the forest root domain should sync with a reliable external source. This matters because Kerberos fails when clocks differ by more than five minutes. If logins break after a DC change, check w32tm /query /status before anything else.

2. A user was just added to a group but still cannot open the share. What is the fastest fix?

> **Answer:** log off and log on again. Group memberships are stored in the Kerberos ticket the user receives at logon. Until they get a new ticket, the file server still sees the old list of groups. Logging off and on works, and so does klist purge followed by accessing the share again. gpupdate /force does not refresh the ticket.

3. Which command shows a summary of AD replication health?

> **Answer:** `repadmin /replsummary`. It lists every domain controller, how many replication attempts failed, and the largest delay since the last successful replication. Broken replication causes strange problems: a password change that works on one DC but not another, or a new user who cannot log in at one site.

All three come back to the basics: time, tickets and replication.

## In one line

> **AD rewards those who know the basics.** Time, tickets and replication explain most AD tickets.

**Check replication now**

```powershell
repadmin /replsummary
```
