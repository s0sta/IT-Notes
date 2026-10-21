---
id: p560
title: "The layers of web request defence"
slug: the-layers-of-web-request-defence
sections: [it, devsecops]
topic: "Application & API security"
tags: [WebSecurity, HTTP, TLS, DevSecOps, AppSec]
source: "LinkedIn post P560 · PythonSec series"
linkedin_date: 2030-04-25
design: stack
---

# The layers of web request defence

A request crosses six layers before your code sees it, and each layer answers a different question. Remove one and the others still stand, but not as high. The order matters: each layer can only act on what the one below passed through.

## Quick reference

*Bottom to top: each layer assumes the one below*

1. **TLS** — Encrypts the hop and gives the client a certificate to verify. · *transport*
2. **HSTS** — Tells the browser to refuse plain HTTP for this host. · *browser policy*
3. **WAF** — Filters known-bad requests at the edge before the app sees them. · *edge filter*
4. **CSP** — Limits where scripts load from and whether inline code runs. · *response policy*
5. **CORS** — Decides which origins may read a response in a browser. · *browser gate*
6. **Cookies and auth** — Who the caller is, and what the token is allowed to do. · *identity*

## Explained

### Bottom to top

TLS encrypts the hop and gives the client a certificate to verify. HSTS tells the browser to refuse plain HTTP for this host, so the next visit cannot be stripped.

The WAF filters known-bad requests at the edge before the application sees them. CSP limits where scripts load from and whether inline code runs.

CORS decides which origins may read a response in a browser. Cookies and auth carry the identity: who the caller is and what the token may do.

### What each cannot do

TLS does not stop an injection. HSTS does not help the first visit. A WAF does not know your business logic. CSP does not fix a server-side bug. CORS does not stop curl. Cookie flags do not encrypt the value. A missing layer is not a finding on its own.

> **The honest caveat:** the layers are not independent. A CDN that terminates TLS sees plaintext, and a WAF bypass says nothing about the code behind it. Each layer assumes the one below did its job.

> **The lesson:** know which layer you are testing before you call it secure.

## In one line

> **Six layers, six ways to fail.** Remove one and the others still stand, but not as high.

**Start at the top**

```bash
curl -sI $URL | head -20
```
