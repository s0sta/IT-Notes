---
id: p554
title: "Four header defences and what each stops"
slug: four-header-defences-and-what-each-stops
sections: [it, devsecops]
topic: "Application & API security"
tags: [HTTP, WebSecurity, DevSecOps, CyberSecurity, CSP]
source: "LinkedIn post P554 · PythonSec series"
linkedin_date: 2030-04-11
design: explainer
---

# Four header defences and what each stops

A scanner gives the site a green tick and a session still leaks. Four response headers close four different doors, and each one is easy to configure badly.

## Quick reference

### 1. HSTS

- Refuses plain HTTP after the first HTTPS visit
- Closes SSL-strip on a hostile network
- max-age 31536000 is one year
- Preload is a browser-list commitment

### 2. CSP

- Allowlists where scripts may load from
- Blocks inline script without a nonce or hash
- Stops an injected tag from executing
- Report-only first, enforce second

### 3. CORS

- Decides which origins may read a response
- The browser enforces it, not the server
- Wildcard plus credentials is invalid
- It is not authentication

### 4. Cookie flags

- Secure keeps the cookie off plain HTTP
- HttpOnly hides it from document.cookie
- SameSite blocks the cross-site send
- Stops script and CSRF from using the token

> **Note:** Four headers, four attacks: none of them replaces another.

## Explained

### HSTS

Strict-Transport-Security tells the browser to refuse plain HTTP for this host for the seconds in max-age. After one clean HTTPS visit it stops an SSL-strip attack, because the browser never offers HTTP again for that period. A max-age of 31536000 is one year, and preload is a separate commitment with the browser vendors.

### CSP

Content-Security-Policy limits where scripts may load from and whether inline script may run. With default-src 'self' and a nonce on the one inline block you need, an injected script tag reaches the page and does not execute.

### CORS

Access-Control-Allow-Origin decides which origins a browser may read a response from. The browser enforces it, not the server: curl ignores CORS completely, so a permissive header is not access control for scripts. A wildcard with credentials is invalid, and browsers say so.

### Cookie flags

Secure keeps the cookie off plain HTTP, HttpOnly hides it from document.cookie, and SameSite stops another site from sending it on a cross-site request. Secure and HttpOnly do different jobs, and one does not imply the other. Together they shrink what an XSS foothold can steal.

> **The honest caveat:** HSTS does nothing on the very first visit, CSP needs a report-only phase before enforcement, and cookie flags do not encrypt the value. Each control leaves a gap the next one does not fill.

> **The lesson:** name the attack each header stops, then test that it does.

## In one line

> **Four headers, four attacks.** Each control closes a door the others leave open.

**Check the headers**

```bash
curl -sI $URL
```
