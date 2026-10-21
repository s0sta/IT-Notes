---
id: p553
title: "The HTTP security header cheat sheet"
slug: the-http-security-header-cheat-sheet
sections: [it, devsecops]
topic: "Application & API security"
tags: [HTTP, Security, DevSecOps, WebSecurity, Curl]
source: "LinkedIn post P553 · PythonSec series"
linkedin_date: 2030-04-09
design: cheatsheet
---

# The HTTP security header cheat sheet

A security review reads the code and skips the response headers. Four blocks of commands read what the browser actually receives, and each block answers a different question.

## Quick reference

### TLS

```bash
curl -sI https://example.com | head -1
openssl s_client -connect example.com:443
openssl x509 -noout -dates -in cert.pem
curl -sI $URL | grep -i strict
```

### CSP

```bash
curl -sI $URL | grep -i content-sec
curl -sI $URL | grep -i x-frame
jq -r ."content-security-policy" h.json
curl -sI $URL | grep -i report-only
```

### CORS

```bash
curl -sI -H 'Origin: https://a.test' $URL
curl -sI -H 'Origin: null' $URL
curl -sI $URL | grep -i access-control
curl -sI $URL | grep -i vary
```

### Cookies

```bash
curl -sI $URL | grep -i set-cookie
curl -sI $URL | grep -i httponly
curl -sI $URL | grep -i samesite
jq -r ."set-cookie" h.json
```

## Explained

### TLS

Export URL=https://example.com once. `curl -sI https://example.com | head -1` shows the status line, `openssl s_client -connect example.com:443` prints the chain, and `openssl x509 -noout -dates -in cert.pem` reads the dates from a saved certificate. `curl -sI $URL | grep -i strict` finds HSTS.

### CSP

`curl -sI $URL | grep -i content-sec` finds the policy, and `grep -i x-frame` checks framing. `jq -r ."content-security-policy" h.json` reads the same header from a dump, and `grep -i report-only` catches a policy that only reports.

### CORS

`curl -sI -H 'Origin: https://a.test' $URL` asks the server to answer a foreign origin. Repeat with Origin: null, which is what a sandboxed frame sends. `grep -i access-control` shows the answer, and `grep -i` vary shows whether caches will mix the two.

### Cookies

`curl -sI $URL | grep -i set-cookie` finds the header. `grep -i` httponly and `grep -i` samesite confirm the flags, and `jq -r ."set-cookie" h.json` lists every cookie from a dump.

> **The honest caveat:** a CDN can add, rewrite or strip any of these headers, so test the hostname users hit, not the origin behind it, and run the blocks against staging before production.

> **The lesson:** read the headers before you believe the diagram.

## In one line

> **Headers are the cheapest control.** Four blocks, one dump, five minutes before the next release.

**Dump the headers**

```bash
curl -sI $URL
```
