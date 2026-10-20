---
id: p302
title: "Zero-trust architecture, drawn"
slug: zero-trust-architecture-drawn
sections: [it, devsecops]
topic: "Security & hardening"
tags: [ZeroTrust, CyberSecurity, CloudSecurity, Identity, DevSecOps]
source: "LinkedIn post P302 · Visual series"
linkedin_date: 2028-08-31
design: architecture
---

# Zero-trust architecture, drawn

A laptop on hotel Wi-Fi asks for the finance database. The VPN says yes because the laptop is on the network, and that is the whole problem with perimeter security.

## Quick reference

- **Tier 1 · Identity:** Identity provider (IDP) · MFA (MFA) · Device posture (DEV)
- **Tier 2 · Policy:** Policy decision point (PDP) · Policy enforcement (PEP)
- **Tier 3 · Resources:** Applications (APP) · Data stores (DATA) · APIs (API)

**Request flow:** Identity provider → MFA → Device posture → Policy decision point → Policy enforcement → Applications → Data stores; Applications → APIs

## Explained

### Identity

The identity provider authenticates the user and issues a short-lived token. MFA proves the human at the keyboard. Device posture answers a different question: is this machine patched, encrypted and enrolled? A stolen password on an unmanaged laptop fails that second check without anyone reading a log.

### Policy

The policy decision point evaluates the token, the device, the resource and the context, then returns allow or deny. The policy enforcement point sits in front of the resource and applies the answer. The decision is made per request, not once per session, so a revoked device loses access on the next call.

### Resources

Applications, data stores and APIs are the resources. Each one is reached through an enforcement point, not through a flat network. The arrows matter: identity feeds policy, policy guards resources, and the resource tier is no longer a trusted segment. Every arrow is a control point.

> **The honest caveat:** this moves the single point of failure to the identity provider. If it is down, nothing authenticates; if it is compromised, every policy decision is made by the attacker.

> **The lesson:** the network stops being the trust boundary, and identity takes its place.

## In one line

> **The network is not the boundary.** Identity is the control plane for every request.

**Trace one request**

```bash
curl -sv https://example.com
```
