---
id: p718
title: "Post-incident commands"
slug: post-incident-commands
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [Python, IncidentResponse, SRE, CommandLine, DevOps]
source: "LinkedIn post P718 · IR series"
linkedin_date: 2031-04-29
design: cheatsheet
---

# Post-incident commands

The incident is closed, the tab is still open, and the commands that would have shortened it are spread across four notes. A sheet is cheaper than a search.

## Quick reference

### Coverage

```bash
python3 detection_gap.py t.json d.json
grep -rl 'T1059' detection/
jq '.[] | select(.enabled)' det.json
git log -1 --format=%cs detection/
```

### Runbooks

```bash
python3 runbook_freshness.py docs/runbooks
find docs/runbooks -name '*.md' -mtime +90
grep -L '^Owner:' docs/runbooks/*.md
git log -1 --format=%cs docs/runbooks/*.md
```

### Alerts

```bash
python3 alert_fatigue.py alerts.json
jq '[.[]|select(.actioned)]|length'
grep -c '"actioned": false' alerts.json
python3 alert_fatigue.py a.json --days 30
```

### Controls

```bash
python3 control_verify.py ctl.json exports
jq '.mfa.enforced' exports/iam.json
aws iam get-account-summary
terraform plan -detailed-exitcode
```

## Explained

### Coverage

`detection_gap.py` compares the technique list with the rules. The grep and jq lines find a technique and show which rules are enabled. git log tells you when the detection directory last changed.

### Runbooks

`runbook_freshness.py` checks dates, owners and links. find checks the file's modification time and grep finds a missing owner line, which are proxies when the tool is not installed. The last line shows the last commit that touched the runbooks.

### Alerts

`alert_fatigue.py` ranks rules by signal. The jq and grep lines count actioned and unactioned alerts in an export. `--days 30` keeps the review to the current month.

### Controls

`control_verify.py` joins the inventory with the exports. The jq line reads one key, the AWS CLI reads the account summary, and `terraform plan -detailed-exitcode` shows whether the infrastructure still matches the code.

### The fix

Paste the sheet into the incident channel at the start of the review. Answer each question with one command, and write down the command that answered it.

### Prevention

Keep the sheet beside the runbooks and update it when a postmortem finds a better command. A sheet nobody edits is a museum.

> **The honest caveat:** the file names are placeholders. Substitute your paths before you trust the output.

> **The lesson:** after the incident, the useful work is the check you can run again.

## In one line

> **Close the incident, open the loop.** The review is four questions, and each one has a command.

**Run the sheet**

```bash
python3 detection_gap.py t.json d.json
```
