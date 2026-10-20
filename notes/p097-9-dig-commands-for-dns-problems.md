---
id: p97
title: "9 dig commands for DNS problems"
slug: 9-dig-commands-for-dns-problems
sections: [it]
topic: "Networking & DNS"
tags: [DNS, Networking, Linux, SysAdmin, Troubleshooting]
source: "LinkedIn post P97 · Linux + IT series"
linkedin_date: 2027-05-11
design: terminal
---

# 9 dig commands for DNS problems

"It is always DNS." Sometimes it is. dig tells you for sure. Nine commands that answer almost every DNS question.

## Quick reference

### What does DNS say?

```bash
# just the answer, nothing else
dig shop.example.com +short
# mail servers, with priority
dig example.com MX +short
# SPF, site verification and other text records
dig example.com TXT +short
```

### Who says what?

```bash
# ask one specific resolver
dig @1.1.1.1 shop.example.com +short
# ask the authoritative server. Different = cache
dig @ns1.example.com shop.example.com +short
# 2843 = seconds left before the cache expires
dig shop.example.com +noall +answer
```

### Follow the whole chain

```bash
# from the root servers down to the answer
dig shop.example.com +trace
# which servers are authoritative
dig example.com NS +short
# reverse lookup: IP to name (PTR)
dig -x 203.0.113.10 +short
```

## Explained

### What does DNS say?

- `dig shop.example.com +short` — only the answer, the IP address, without the rest of the output.
- `dig example.com MX +short` — the mail servers for a domain and their priority. Lower number, higher priority.
- `dig example.com TXT +short` — text records: SPF, DKIM selectors, domain verification codes. Most email delivery problems start here.

### Who says what?

- `dig @1.1.1.1 shop.example.com +short` — ask one specific resolver instead of your default. Compare 1.1.1.1, 8.8.8.8 and your company DNS to see who is out of date.
- `dig @ns1.example.com shop.example.com +short` — ask the authoritative nameserver directly. If it gives a different answer than the public resolvers, they are still serving a cached value.
- `dig shop.example.com +noall +answer` — shows the TTL. That number is how many seconds the cached answer will live. It tells you how long you have to wait after a change.

### Follow the whole chain

- `dig shop.example.com +trace` — follows the lookup from the root servers, to .com, to your nameservers, to the final answer. Broken delegation shows up clearly here.
- `dig example.com NS +short` — the authoritative nameservers. After a migration, check they point where you think.
- `dig -x 203.0.113.10 +short` — the reverse lookup, IP to name. Mail servers with no matching PTR record often land in spam.

The three facts that solve most DNS mysteries: the answer, which server gave it, and the TTL.

## In one line

> **Check the answer, the server, the TTL.** Three facts that solve most DNS mysteries.

**Try it**

```bash
dig shop.example.com +short
```
