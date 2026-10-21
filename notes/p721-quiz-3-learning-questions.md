---
id: p721
title: "Quiz: 3 learning questions"
slug: quiz-3-learning-questions
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [Python, IncidentResponse, SRE, DevOps, CyberSecurity]
source: "LinkedIn post P721 · IR series"
linkedin_date: 2031-05-06
design: quiz
---

# Quiz: 3 learning questions

Three questions close the series, and each one is about proof you cannot see from a dashboard. Answer before the reveal.

## Quick reference

**Q1. Why is detection coverage a list, not a feeling?**

- a) Because auditors ask for one
- b) Because every technique is covered or not
- c) Because feelings are hard to document

> **Answer:** b) Because every technique is covered or not. A list names each technique and its rule. Gaps are rows with no enabled rule, and each can be counted, assigned and checked. A feeling cannot be reviewed.

**Q2. What makes an alert actionable?**

- a) A named owner, a runbook and a signal
- b) A high severity label
- c) A dashboard that updates quickly

> **Answer:** a) A named owner, a runbook and a signal. An owner, a runbook and a signal ratio worth acting on. Severity is a label; action is a person with a next step. Fifty fires, two actions: the team ignores it.

**Q3. Why does a control need evidence?**

- a) Because the vendor says so
- b) Because the policy and the state can differ
- c) Because screenshots look professional

> **Answer:** b) Because the policy and the state can differ. A policy states intent; an export states fact. Without a file and a key, enabled is a belief, and a control can stay off for months. Evidence is the difference.

## Explained

### Question one

Why is detection coverage a list, not a feeling? Because a list names every technique and the rule that covers it. The gaps are rows with no enabled rule, and each row can be counted, assigned and checked again next week. A feeling cannot be reviewed.

### Question two

What makes an alert actionable? A named owner, a runbook and a signal ratio that says the page is not noise. Severity is a label; action is a person with a next step. A rule that fires fifty times and is actioned twice is training the team to ignore the pager.

### Question three

Why does a control need evidence? Because a policy states intent and an export states fact. Without a dated file and a key, "enabled" is a belief, and a disabled control can survive a quarter of reviews. The evidence is the difference between claiming and checking.

> **The honest caveat:** passing this quiz does not make the loop work; the schedule, the owners and the evidence do.

> **The lesson:** prevention is a check you can show.

That is the series. Fifty posts, five phases and twenty-five Python scripts, from the first alert to this quiz. Thank you for following along.

## In one line

> **Prevent it, then prove it.** Fifty posts, five phases and twenty-five Python scripts.

**Keep the loop:** schedule the four checks
