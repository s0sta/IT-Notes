---
id: p488
title: "Anatomy of a DNS record"
slug: anatomy-of-a-dns-record
sections: [it, devsecops]
topic: "Networking & DNS"
tags: [DNS, Networking, SysAdmin, DevOps, Infrastructure]
source: "LinkedIn post P488 · Network series"
linkedin_date: 2029-11-08
design: anatomy
---

# Anatomy of a DNS record

An answer line looks like five fields in a row: api.example.com. 300 IN A 203.0.113.10. Read them left to right and the record stops being a mystery.

## Quick reference

```text
api.example.com. 300 IN A 203.0.113.10
```

| Part | Name | What it means |
|:--|:--|:--|
| `api.example.com.` | The name | Fully qualified: the trailing dot stops the search list. |
| `300` | The TTL | Seconds a cache may keep it. 300 is five minutes. |
| `IN` | The class | Internet. The only class you will meet in practice. |
| `A` | The type | An IPv4 address record. AAAA is the IPv6 version. |
| `203.0.113.10` | The value | Documentation range, RFC 5737: never a real host. |

## Explained

### The five fields

The name is fully qualified because of the trailing dot. Without it, the resolver may append a search domain and ask for api.example.com.corp.example.

The TTL is 300 seconds: the longest a cache may keep this answer before asking again. The class is IN, the internet class, and the only one you will meet.

The type is A, which means one IPv4 address. The value is 203.0.113.10, from the documentation range, so it is safe to print and not a public host.

### What the line does not say

It does not show the CNAME chain that produced the name, the signature that DNSSEC would add, or the resolver that answered. Those live in the full dig output, not in the answer line.

It also does not promise the TTL you see is the zone's TTL. A cache counts down, so a record with 300 in the zone can arrive with 42.

> **The honest caveat:** a short answer is a snapshot, not a history; if you need to know why a name points where it does, read the whole response.

> **The lesson:** five fields, one line, and every DNS argument gets shorter once you can name them.

## In one line

> **The dot ends the name.** A name without its trailing dot is a search-domain accident.

**Read the answer**

```bash
dig api.example.com A
```
