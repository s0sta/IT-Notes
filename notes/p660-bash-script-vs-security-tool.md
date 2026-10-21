---
id: p660
title: "Bash script vs security tool"
slug: bash-script-vs-security-tool
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Bash, DevSecOps, CyberSecurity, Automation, SecOps]
source: "LinkedIn post P660 · ShellSec series"
linkedin_date: 2030-12-15
design: compare
---

# Bash script vs security tool

Every security team argues: write the check in bash, or buy the tool. The honest answer is that they answer different questions.

## Quick reference

| | **BASH** | **TOOL** |
|:--|:--|:--|
| Install | Already on the box | Agent, licence, rollout |
| Scope | The check you wrote | The catalogue it ships |
| Noise | Yours to tune | Rules, not your context |
| Evidence | stdout and exit code | Dashboard and tickets |
| Speed | Seconds, no daemon | Minutes, a pipeline |
| Best for | One host, one question | Fleet, audit, coverage |

**BASH** (The check you wrote): Runs on the host you are on, in the minute you think of the check.

```bash
find / -perm -4000 -type f
```

**TOOL** (The catalogue you buy): Ships hundreds of rules, a fleet view and an audit trail.

```bash
trivy image api:1.4
```

- Bash → the host you are on, now.
- Tool → the fleet, the audit, the rules.

## Explained

### The script

Bash is already on the box. It reads the files and logs the host exposes, applies the rule you wrote, prints a line and exits non-zero. It has no agent, no database and no licence, and it runs in the same minute you think of the check. The cost is that you own the rule, the false positives and the maintenance.

### The tool

A security tool ships a catalogue: hundreds of rules, a parser per format, a fleet view and an audit trail. It knows the checks you did not think of, and it keeps the evidence in one place. The cost is the agent, the licence, the rollout and the tuning, and the rule you need may still be missing.

### Where they meet

The rows line up the trade. Bash is best at one host and one question, the thing you need at 03:00. A tool is best at fleet coverage and audit, the thing you need at quarter end. Neither replaces the other: the script catches the host-specific regression the tool has no rule for, and the tool catches the class of problem the script was never written to see.

> **The honest caveat:** a script with no owner rots faster than a tool with no licence.

> **The lesson:** use the tool for coverage, and write the script for the question only your host can ask.

Cover the fleet.  
Script the edge.
