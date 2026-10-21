---
id: p483
title: "The DNS records cheat sheet"
slug: the-dns-records-cheat-sheet
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, Networking, SysAdmin, DevOps, CheatSheet]
source: "LinkedIn post P483 · Network series"
linkedin_date: 2029-10-28
design: cheatsheet
---

# The DNS records cheat sheet

A record change went out at noon and the old address is still answering at four. Nobody is lying; the answer is cached.

## Quick reference

### Address

```bash
dig example.com A +short
dig example.com AAAA +short
dig example.com A +noall +answer
dig @1.1.1.1 example.com A
dig example.com AAAA +noall +answer
```

### Alias

```bash
dig www.example.com CNAME +short
dig example.com NS +short
dig www.example.com CNAME +noall +answer
dig +trace example.com
dig www.example.com A +short
```

### Mail

```bash
dig example.com MX +short
dig example.com TXT +short
dig _dmarc.example.com TXT +short
dig default._domainkey.example.com TXT
dig example.com MX +noall +answer
```

### Policy

```bash
dig example.com CAA +short
dig example.com DS +short
dig example.com DNSKEY +short
dig +dnssec example.com A
dig example.com SOA +short
```

## Explained

### Address

An A record holds one IPv4 address, and AAAA holds one IPv6 address. Ask with `dig example.com A +short` and you get the value alone; drop +short when you need the TTL and the section it came from.

A second resolver is a second opinion. `dig @1.1.1.1 example.com A` asks Cloudflare instead of your local resolver, which separates a zone problem from a cache problem.

### Alias

A CNAME points one name at another and must be the only data record at that name. `dig www.example.com CNAME +short` shows the target. NS shows the delegation, and `dig +trace example.com` walks root, TLD and zone in one command. `dig www.example.com A +short` shows what the chain resolves to.

### Mail

MX carries a preference and a mail host. TXT carries SPF and other policy text; DMARC lives at _dmarc.example.com, and DKIM at selector._domainkey.example.com.

### Policy

CAA names the certificate authorities allowed to issue for the name and its subdomains. DS and DNSKEY build the DNSSEC chain, and +dnssec asks for the signatures. SOA holds the serial and the negative-cache timer.

> **The honest caveat:** +short prints only the answer data, so it hides the TTL, the class and the authority section; use the full answer when the question is why.

> **The lesson:** read the record type before you read the record.

## In one line

> **Read the record, not the rumour.** A query is evidence; a dashboard screenshot is not.

**Check the delegation**

```bash
dig +trace example.com
```
