---
id: p84
title: "9 openssl commands for SSL certificate problems"
slug: 9-openssl-commands-for-ssl-certificate-problems
sections: [it, devsecops]
topic: "Web servers, TLS & HTTP"
tags: [SSL, TLS, Linux, CyberSecurity, SysAdmin]
source: "LinkedIn post P84 · Linux series"
linkedin_date: 2027-04-11
design: terminal
---

# 9 openssl commands for SSL certificate problems

"Your connection is not private." When a certificate breaks, the browser tells users there is a problem but not what it is. openssl tells you exactly. Nine commands for every certificate problem.

## Quick reference

### What certificate is live?

```bash
# connect like a browser. -servername sends SNI
openssl s_client -connect shop.example.com:443 -servername shop.example.com
# valid from, valid until
openssl x509 -in cert.pem -noout -dates
# the names it covers. Browsers check these
openssl x509 -in cert.pem -noout -ext subjectAltName
```

### Why does the browser complain?

```bash
# expires within 30 days? Exit code 1 means yes
openssl x509 -in cert.pem -noout -checkend 2592000
# is the chain complete? A missing intermediate fails here
openssl verify -CAfile chain.pem cert.pem
# run the same on the key (rsa). The hashes must match
openssl x509 -noout -modulus -in cert.pem | openssl md5
```

### A new key and request

```bash
# new private key + CSR for the certificate authority
openssl req -new -newkey rsa:2048 -nodes -keyout shop.key -out shop.csr
# check the CSR before you submit it
openssl req -in shop.csr -noout -subject
# Let's Encrypt: every certificate and its expiry
certbot certificates
```

## Explained

### What certificate is live?

- `openssl s_client -connect shop.example.com:443 -servername shop.example.com` — connects like a browser and shows the certificate the server really sends. The -servername part sends SNI, which matters when one server hosts many sites.
- `openssl x509 -in cert.pem -noout -dates` — when the certificate starts and when it expires.
- `openssl x509 -in cert.pem -noout -ext subjectAltName` — the names it is valid for. Browsers check this list, not the old Common Name field.

### Why does the browser complain?

- `openssl x509 -in cert.pem -noout -checkend 2592000` — does it expire within the next 30 days? The exit code makes this easy to use in a monitoring script.
- `openssl verify -CAfile chain.pem cert.pem` — is the chain complete? A missing intermediate certificate is the classic "works in Chrome, fails on Android and in curl".
- `openssl x509 -noout -modulus -in cert.pem | openssl md5` — run the same with openssl rsa on the key file. If the two hashes differ, the key and certificate do not belong together, and nginx will refuse to start.

### A new key and request

- `openssl req -new -newkey rsa:2048 -nodes -keyout shop.key -out shop.csr` — a new private key and a certificate signing request to send to your certificate authority.
- `openssl req -in shop.csr -noout -subject` — check the names in the CSR before you submit it.
- `certbot certificates` — for Let's Encrypt: every certificate and the days it has left.

## In one line

> **Expiry is a date. Watch it.** Monitor it, renew it automatically, and never be surprised.

**Try it**

```bash
openssl x509 -in cert.pem -noout -enddate
```
