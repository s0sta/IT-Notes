---
id: p589
title: "Four identity failures"
slug: four-identity-failures
sections: [it, devsecops]
topic: "Security & hardening"
tags: [Identity, CyberSecurity, TLS, DevSecOps, AccessControl]
source: "LinkedIn post P589 · PythonFixes series"
linkedin_date: 2030-07-02
design: explainer
---

# Four identity failures

Four failures, one shape: a credential that outlived the decision that created it.

## Quick reference

### Expired certificate

- The monitor watched the repository copy
- Clients fail closed on the date
- Renew 21 days before notAfter

### Stale key

- Rotation added a key, not removed one
- The old key still decrypts
- Test revocation, not just creation

### Leaver access

- HR closed the ticket, not the account
- A login came after the last day
- Join leavers to the access export

### Old password

- No expiry and no owner
- One hash copied across hosts
- Age is a prompt, not proof

> **Note:** Four failures, one shape: a credential that outlived the decision that created it.

## Explained

### Expired certificate

The date passed quietly. Clients fail closed, the error names the host, and the first instinct is to blame the client. The monitor was watching a copy in a repository, not the certificate the ingress served. Renew three weeks before the date and check the served file, not the source.

### Stale key

Rotation created a second key, and the first one kept working. Two copies, one revocation that was never tested, and a decrypt path nobody owned. A key is not rotated until the old one is deleted and the service proves it cannot use it. Test the revocation, not the creation.

### Leaver access

HR closed the ticket and the account stayed active. The last login came after the last day, and no export joined the two facts. This is not a phishing problem; it is a join that nobody ran. Run the audit on the leaver event, then again from cron.

### Old password

No expiry, no owner, one hash copied across hosts, and a wiki page that remembers it. Age is a prompt, not proof: a fresh password can be shared and an old one can be strong. Age is still the cheapest signal you have.

> **The honest caveat:** none of these is caught by a vulnerability scanner, because each one is a valid credential used at the wrong time or by the wrong person.

> **The lesson:** identity fails quietly, on a date.

## In one line

> **Nothing is broken; it is only old.** Each failure is a valid credential used at the wrong time.

**Join the exports**

```bash
python3 offboarding_audit.py
```
