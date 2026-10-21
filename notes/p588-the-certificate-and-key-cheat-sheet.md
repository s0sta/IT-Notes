---
id: p588
title: "The certificate and key cheat sheet"
slug: the-certificate-and-key-cheat-sheet
sections: [it, devsecops]
topic: "Security & hardening"
tags: [OpenSSL, TLS, DevSecOps, Linux, CyberSecurity]
source: "LinkedIn post P588 · PythonFixes series"
linkedin_date: 2030-06-30
design: cheatsheet
---

# The certificate and key cheat sheet

A certificate alert gives you four questions: what is in the file, does it verify, what format is it in, and which key belongs to it.

## Quick reference

### Inspect

```bash
openssl x509 -in cert.pem -noout -text
openssl x509 -in cert.pem -noout -dates
openssl x509 -in cert.pem -noout -subject
openssl x509 -in cert.pem -noout -issuer
openssl s_client -connect api:443
```

### Verify

```bash
openssl verify -CAfile root.pem leaf.pem
openssl verify -untrusted mid.pem leaf.pem
openssl verify -purpose sslserver leaf.pem
openssl verify -x509_strict leaf.pem
```

### Convert

```bash
openssl x509 -in cert.pem -outform der
openssl x509 -inform der -in cert.der
openssl pkcs12 -in bundle.p12 -nokeys
openssl pkcs12 -in bundle.p12 -nocerts
openssl pkcs8 -topk8 -nocrypt -in key.pem
```

### Keys

```bash
openssl genpkey -algorithm RSA
openssl req -new -key key.pem -out req.csr
openssl req -in req.csr -noout -text
ssh-keygen -t ed25519 -C "ops@host"
ssh-keygen -y -f ~/.ssh/id_ed25519
```

## Explained

### Inspect

`openssl x509 -in cert.pem -noout -text` prints the subject, issuer, dates, SANs and extensions. -dates, -subject and -issuer give one field each when the full text is too much. `openssl s_client -connect api:443` shows what the server sends, often a different file from the one you edited.

### Verify

`openssl verify -CAfile root.pem leaf.pem` builds the path from the trust anchor. -untrusted `mid.pem` supplies the intermediate when it is not in the trust store. -purpose sslserver checks the certificate for that role, and -x509_strict disables the legacy workarounds.

### Convert

`openssl x509 -in cert.pem -outform der` and -inform der -in cert.der move between PEM and DER. The pkcs12 commands extract certificates with -nokeys and keys with -nocerts. `openssl pkcs8 -topk8 -nocrypt -in key.pem` converts a key to the format some services demand.

### Keys

`openssl genpkey -algorithm RSA` creates a key; `openssl req -new -key key.pem -out req.csr` creates the request, and `openssl req -in req.csr -noout -text` reads it back. `ssh-keygen -t ed25519 -C "ops@host"` makes an SSH key, and `ssh-keygen -y -f ~/.ssh/id_ed25519` prints its public half.

> **The honest caveat:** -text prints the public key and the signature, never the private key. The command that prints private key material is pkcs12 -nodes, so keep it out of a shared terminal.

> **The lesson:** read the file before you renew it, and read the command before you run it.

## In one line

> **Read the file before you renew it.** Four blocks that turn a certificate alert into a command.

**Verify the chain**

```bash
openssl verify -CAfile root.pem leaf.pem
```
