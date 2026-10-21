---
id: p707
title: "The evidence path"
slug: the-evidence-path
sections: [it, devsecops]
topic: "Incident response & detection"
tags: [IncidentResponse, DFIR, CyberSecurity, SRE, Forensics]
source: "LinkedIn post P707 · IR series"
linkedin_date: 2031-04-03
design: architecture
---

# The evidence path

An incident review asks for the evidence and gets a folder of files with no order, no digests and no list. The drawn path is the order: collect, preserve, present.

## Quick reference

- **Collect:** Case directory (CASE) · Process export (PS) · Network export (SS) · Logs and config (LOG)
- **Preserve:** SHA-256 per file (HASH) · Manifest (MAN) · Sealed bundle (STORE)
- **Present:** Timeline (TIME) · Report (RPT) · Review (REV)

**Request flow:** Case directory → SHA-256 per file → Manifest → Sealed bundle → Timeline → Review; Sealed bundle → Report → Review; Process export → SHA-256 per file; Network export → SHA-256 per file; Logs and config → SHA-256 per file

**Around it:** sha256sum (SHA) · ps -eo (PS) · ss -tanp (SS) · evidence_collect.py (PY)

## Explained

### Collect

The first tier holds the case directory, the process export, the network export and the logs. Collection is a capture, not an investigation: take the files, the running processes and the sockets first, because processes and connections disappear on reboot and a copied file can wait.

### Preserve

The second tier hashes every artefact, writes the manifest and seals the bundle. One digest per file, one bundle hash over all of them, and the manifest kept with the bundle. This is the tier that makes the rest defensible, because it is the only one that can prove nothing changed.

### Present

The third tier is the timeline, the report and the review. It reads from the preserved bundle, never from the live host, and every row points back to an evidence id.

### Read it in order

The poster draws the three bands top to bottom, with arrows from each collected artefact to the hash, then to the manifest and the sealed store, then to the timeline and the report. Four chips at the bottom name the tools: sha256sum, ps, ss and the collector.

> **The honest caveat:** no diagram survives a host that was rebooted before collection; the first tier is the one you cannot redo.

> **The lesson:** collect, then hash, then say it.

## In one line

> **Collect, then hash, then say it.** Nothing after the reboot can rebuild the first tier.

**Seal the bundle**

```bash
python3 evidence_collect.py /cases
```
