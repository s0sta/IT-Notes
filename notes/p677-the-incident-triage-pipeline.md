---
id: p677
title: "The incident triage pipeline"
slug: the-incident-triage-pipeline
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, SRE, DevOps, OnCall, CyberSecurity]
source: "LinkedIn post P677 · IR series"
linkedin_date: 2031-01-23
design: architecture
---

# The incident triage pipeline

A page is a signal, not an incident. Between the two sits a pipeline that decides whether anyone should be woken, what the incident is called, and who owns it.

## Quick reference

- **Signal:** Alert rule (RULE) · On-call page (PAGE)
- **Triage:** Dedupe (DEDUP) · Severity policy (SEV)
- **Decide:** Declare incident (DECL) · Assign owner (OWNER)

**Request flow:** Alert rule → Dedupe → Severity policy → Declare incident → Assign owner; On-call page → Dedupe

**Around it:** Runbook (RUN) · Timeline (TIME) · Status page (STAT)

## Explained

### Signal

Two surfaces arrive first: the alert rule and the on-call page. They carry a fingerprint, a rule, a severity and a start time. Neither may declare an incident. Their job is to start the clock and open the runbook, because the first fact of any incident is when it began.

### Triage

Triage is where the noise dies. Dedupe groups repeated fingerprints, so eleven alerts become five incidents. The severity policy turns users, data, revenue and duration into one number, and shows where the declared number disagrees. The output is a short list of real incidents, ranked.

### Decide

Decide is a human step with two moves: declare the incident and assign one owner. The declaration names the severity, the incident id and the channel. The owner is the person who will run the timeline, not the person who happened to be in the channel first.

The three tiers are deliberately narrow. Signal cannot decide, triage cannot act, and decide cannot investigate. A pipeline that lets one tier do all three is a hero culture with better diagrams.

> **The honest caveat:** a pipeline that nobody can skip becomes a queue. Keep a break-glass path for the obvious SEV1, and record why it was used.

> **The lesson:** a page becomes an incident only when someone decides it is one.

## In one line

> **Signal, triage, then decide.** Three tiers, and only the last one may declare.

**Declare one owner:** pd incident:create -S api -t API
