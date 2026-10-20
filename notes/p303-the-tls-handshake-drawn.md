---
id: p303
title: "The TLS handshake, drawn"
slug: the-tls-handshake-drawn
sections: [it, devsecops]
topic: "Web servers, TLS & HTTP"
tags: [TLS, Networking, CyberSecurity, HTTPS, DevOps]
source: "LinkedIn post P303 · Visual series"
linkedin_date: 2028-09-03
design: explainer
---

# The TLS handshake, drawn

You reload nginx with a new certificate and curl returns a handshake error. The failure is in one of four steps, and the error text usually names which. The sequence below is TLS 1.2, the easiest to read in a capture.

## Quick reference

### ClientHello

- Client random, versions, cipher suites
- SNI carries the hostname in the clear
- Server picks the version and cipher
- One round trip before any secret

### Certificate

- Server sends its certificate chain
- Client checks root, dates, hostname
- OCSP or CRL answers on revocation
- A bad chain stops the handshake

### Key exchange

- ECDHE shares are ephemeral
- Both sides derive the same secret
- Certificate key signs the exchange
- Session keys are symmetric

### Finished

- ChangeCipherSpec switches the keys
- Finished covers the handshake transcript
- TLS 1.3 does it in one round trip
- Records are encrypted from here

## Explained

### ClientHello

The client sends a random value, the TLS versions it supports, its cipher suites, and the server name in SNI. The server answers with its own random value, version and cipher. Nothing is encrypted yet, so the hostname is visible on the wire.

### Certificate

The server sends its certificate chain. The client checks the chain to a trusted root, the dates, the hostname, and the revocation status through OCSP or a CRL. A missing intermediate or an expired leaf ends the connection before any key is derived.

### Key exchange

With ECDHE, each side sends an ephemeral public share and both derive the same secret. The certificate signature proves the server holds the private key behind the certificate. Session keys are symmetric, because public-key operations are slow and symmetric ciphers are not.

### Finished

Each side sends ChangeCipherSpec, then a Finished message that covers the handshake transcript, so a modified hello or cipher list breaks the check. From there, every record is encrypted. TLS 1.3 collapses this into one round trip and encrypts the certificate, but the four jobs are the same.

> **The honest caveat:** a valid certificate proves the domain, not the business behind it. Phishing sites have padlocks too.

> **The lesson:** every TLS error belongs to hello, certificate, key exchange or finished.

## In one line

> **A padlock is a finished handshake.** Encryption is the result, not the whole story.

**Inspect a chain**

```bash
openssl s_client -connect example.com:443
```
