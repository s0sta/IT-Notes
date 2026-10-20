---
id: p101
title: "How an email gets from sender to inbox"
slug: how-an-email-gets-from-sender-to-inbox
sections: [it]
topic: "Networking & DNS"
tags: [Email, DNS, CyberSecurity, ITSupport, SysAdmin]
source: "LinkedIn post P101 · Linux + IT series"
linkedin_date: 2027-05-20
design: pipeline
---

# How an email gets from sender to inbox

"The email was sent" and "the email arrived in the inbox" are two very different things. Six stages sit between them.

## Quick reference

1. **Client submits the mail** — Outlook or your app sends it to the outgoing server. · `:587`
2. **Sender looks up MX** — DNS says which server accepts mail for the domain. · *MX record*
3. **SMTP handoff with TLS** — The two mail servers connect and talk SMTP. · *STARTTLS*
4. **SPF and DKIM checks** — Is this server allowed? Is the signature valid? · *SPF + DKIM*
5. **DMARC decides** — If both checks fail, the domain policy says what to do. · `p=reject`
6. **Spam filter, then inbox** — Content and reputation decide: inbox or junk. · *inbox*

## Explained

1. **The client submits the mail.** Outlook, a phone or your application sends the message to its outgoing mail server on port 587, with a login and TLS.

2. **The sending server looks up MX.** It asks DNS for the MX records of the recipient's domain. These say which server accepts mail for that domain. A wrong MX record means mail goes nowhere, or to the wrong place.

3. **SMTP handoff with TLS.** The sending server connects to the receiving server on port 25 and, ideally, upgrades the connection with STARTTLS. The message is now handed over.

4. **SPF and DKIM checks.** The receiving server checks SPF: is this sending IP listed in the domain's SPF record? And DKIM: does the cryptographic signature in the header match the public key published in DNS?

5. **DMARC decides.** DMARC requires that SPF or DKIM pass and match the visible From domain. If they do not, the domain's DMARC policy says what to do: p=none to only report, p=quarantine for the junk folder, p=reject to refuse the message.

6. **Spam filter, then inbox.** Even fully authenticated mail is scored on content, links, sending reputation and user behaviour. That decides inbox or junk.

The practical lesson: a new website or system that sends email from your domain must be added to SPF and set up with DKIM. Otherwise its mail fails DMARC, and the customer never sees the order confirmation.

## In one line

> **Delivered is not the same as inbox.** SPF, DKIM and DMARC decide which one you get.

**Check your domain**

```bash
dig example.com TXT +short
```
