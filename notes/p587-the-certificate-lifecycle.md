---
id: p587
title: "The certificate lifecycle"
slug: the-certificate-lifecycle
sections: [it, devsecops]
topic: "Security & hardening"
tags: [TLS, PKI, DevSecOps, CloudNative, CyberSecurity]
source: "LinkedIn post P587 · PythonFixes series"
linkedin_date: 2030-06-27
design: architecture
---

# The certificate lifecycle

A certificate is not a file you create once and forget. It is a loop with three tiers, and each tier has its own way to fail.

## Quick reference

- **Issue:** CSR (CSR) · Private CA (CA)
- **Deploy:** Secret store (K8S) · Ingress (TLS)
- **Renew:** Expiry monitor (MON) · Rotator (JOB)

**Request flow:** CSR → Private CA → Secret store → Ingress → Expiry monitor → Rotator → CSR

## Explained

### Issue

A service generates a CSR with the names it will serve, and a private CA signs it with a short lifetime. The failure here is a CSR with the wrong subject or a CA that signs for a year because a default was never changed. The diagram starts at the CSR and ends at the CA.

### Deploy

The signed certificate and its key go into a secret store. The ingress mounts the pair and terminates TLS. The failure here is a secret that holds the key but not the intermediate, or a pod that keeps the old secret after the update. The arrow runs from the CA to the secret, then to the ingress.

### Renew

An expiry monitor watches the certificate the ingress serves, not the one in the repository. When the date comes inside the window, a rotator requests a new certificate and redeploys the secret. The loop closes from the monitor to the rotator to the CSR.

> **The honest caveat:** automation removes the calendar but adds a new failure. A rotator with the wrong permissions can replace a valid certificate with a broken one, so the deploy still needs the bundle check.

> **The lesson:** issue, deploy, renew: three tiers, one loop, no forgotten date.

## In one line

> **A certificate is a loop, not a file.** Every tier has a date, an owner and a way to go stale.

**Check the dates**

```bash
python3 cert_bundle_check.py chain.pem
```
