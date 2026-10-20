---
id: p123
title: "How a Let's Encrypt certificate is issued and renewed"
slug: how-a-lets-encrypt-certificate-is-issued-and-renewed
sections: [it, devsecops]
topic: "Web servers, TLS & HTTP"
tags: [SSL, TLS, LetsEncrypt, Linux, WebSecurity]
source: "LinkedIn post P123 · Linux + IT series"
linkedin_date: 2027-07-11
design: pipeline
---

# How a Let's Encrypt certificate is issued and renewed

Let's Encrypt made HTTPS free for everyone. Understanding the six steps behind it explains why renewals sometimes fail, and how to make sure they do not.

## Quick reference

1. **Account and order** — certbot asks Let's Encrypt for a certificate. · `certbot`
2. **Challenge token** — Let's Encrypt replies: prove you control this domain. · *HTTP-01*
3. **Token served on port 80** — certbot places it under /.well-known/. · `:80`
4. **Let's Encrypt validates** — It fetches the token from several locations. · *validated*
5. **Certificate issued** — Currently valid for 90 days. nginx uses it. · *90 days*
6. **Automatic renewal** — A timer renews with 30 days left, then reloads. · `certbot.timer`

## Explained

1. **Account and order.** certbot, or another ACME client, registers an account and asks Let's Encrypt for a certificate for shop.example.com.

2. **Challenge token.** Let's Encrypt does not take your word for it. It replies with a challenge: prove you control this domain. The most common type is HTTP-01.

3. **Token served on port 80.** certbot places a token file under /.well-known/acme-challenge/ on your web server. This is why port 80 must be reachable from the internet, even if the site redirects everything to HTTPS.

4. **Let's Encrypt validates.** It fetches the token over HTTP, from several network locations at once. If the file is there and correct, the domain is proven. A firewall blocking port 80, a wrong DNS record, or a redirect rule that sends the challenge somewhere else makes this step fail.

5. **Certificate issued.** The certificate is currently valid for 90 days, with shorter lifetimes announced for the future. certbot saves it and configures nginx to use it.

6. **Automatic renewal.** A systemd timer or cron job runs certbot renew twice a day. It renews when a certificate has 30 days or less left, then a deploy hook reloads nginx so the new certificate is actually served.

Most expired certificate incidents come from step 3, 4 or 6: port 80 closed, DNS moved, or nginx never reloaded.

`certbot renew --dry-run` tests the whole chain without issuing anything.

Free certificates, automated renewals, as long as port 80 and the timer keep working.

## In one line

> **Free certificates. Automated renewals.** As long as port 80 and the timer keep working.

**Test renewal now**

```bash
certbot renew --dry-run
```
