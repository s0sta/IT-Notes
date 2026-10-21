---
id: p638
title: "The openssl shell cheat sheet"
slug: the-openssl-shell-cheat-sheet
sections: [it, devsecops]
topic: "Security & hardening"
tags: [OpenSSL, SSH, Linux, DevSecOps, CommandLine]
source: "LinkedIn post P638 · ShellSec series"
linkedin_date: 2030-10-24
design: cheatsheet
---

# The openssl shell cheat sheet

Most openssl questions are one of four: what is in this file, do I trust it, how do I convert it, and which key is this. Four blocks, in that order.

## Quick reference

### Inspect

```bash
openssl x509 -in cert.pem -noout -subject
openssl x509 -in cert.pem -noout -dates
openssl x509 -in cert.pem -noout -text
openssl s_client -connect host:443
```

### Verify

```bash
openssl verify -CAfile ca.pem cert.pem
openssl verify -untrusted int.pem cert
openssl x509 -in cert.pem -checkend 0
openssl x509 -in cert.pem -checkend 86400
openssl crl -in crl.pem -noout -text
```

### Convert

```bash
openssl x509 -inform der -in c.der
openssl x509 -in cert.pem -outform der
openssl pkcs12 -in b.p12 -out b.pem
openssl pkcs12 -in b.p12 -clcerts -nokeys
openssl pkey -in k.pem -pubout
```

### Keys

```bash
ssh-keygen -t ed25519 -C "you@host"
ssh-keygen -lf ~/.ssh/id_ed25519.pub
ssh-keygen -y -f ~/.ssh/id_ed25519
ssh-keygen -F host.example.com
ssh-keygen -R host.example.com
ssh -Q key
```

## Explained

### Inspect

`openssl x509 -in cert.pem -noout -subject` prints the subject, -dates prints notBefore and notAfter, and -text prints everything, including the public key and extensions. `openssl s_client -connect host:443` opens a TLS connection and prints the certificate chain it receives.

### Verify

`openssl verify -CAfile ca.pem cert.pem` checks a leaf against a root. -untrusted `int.pem` supplies the intermediate. `openssl x509 -checkend 0` fails when expired; -checkend 86400 fails within a day. `openssl crl -in crl.pem -noout -text` reads a revocation list.

### Convert

`openssl x509 -inform der -in c.der` prints a DER certificate as PEM. `openssl x509 -in cert.pem -outform der` writes the reverse. `openssl pkcs12 -in b.p12 -out b.pem` exports a PKCS12 bundle; -clcerts -nokeys keeps only the client certificate. `openssl pkey -in k.pem -pubout` derives the public key.

### Keys

`ssh-keygen -t ed25519 -C "you@host"` makes a key with a comment you can trace. `ssh-keygen -lf` prints a fingerprint without printing the key. `ssh-keygen -y -f` prints only the public half of a private key. `ssh-keygen -F` and -R search and remove host keys; `ssh -Q key` lists the algorithms this client supports.

> **The honest caveat:** -text prints public data, but a private key in the same directory is still one careless cat away. Never paste a private key into a ticket.

> **The lesson:** read the certificate before you trust the connection.

## In one line

> **Read the cert, then trust it.** Every command here inspects or converts; none of them signs a certificate.

**Inspect first**

```bash
openssl x509 -in cert.pem -noout -text
```
