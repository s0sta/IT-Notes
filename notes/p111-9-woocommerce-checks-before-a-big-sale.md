---
id: p111
title: "9 WooCommerce checks before a big sale"
slug: 9-woocommerce-checks-before-a-big-sale
sections: [it]
topic: "Web servers, TLS & HTTP"
tags: [WooCommerce, WordPress, Ecommerce, WebPerformance, SysAdmin]
source: "LinkedIn post P111 · Linux + IT series"
linkedin_date: 2027-06-13
design: checklist
---

# 9 WooCommerce checks before a big sale

I look after a bilingual WooCommerce store with about 1,400 products. A big sale is when small problems become expensive, because every minute of a broken checkout is lost orders. Nine checks for the week before.

## Quick reference

### The store

- **Stock and prices right** — export, then spot-check
- **Test order end to end** — every payment method
- **Coupons tested** — dates, limits, exclusions

### The server

- **Checkout not cached** — exclude cart, checkout, account
- **Fresh backup** — files + database, restore tested
- **Room to grow** — CPU, RAM and PHP workers

### The day itself

- **Updates frozen** — no plugin updates on sale day
- **Uptime monitor on** — the checkout page, every minute
- **Someone on call** — with hosting and payment contacts

## Explained

### The store

- **Stock and prices right** — export the products, check the sale prices and stock levels against the plan. A wrong price at scale is hard to undo.
- **Test order end to end** — place a real order with every payment method you offer, and follow it all the way: payment, confirmation email, order status, stock reduction.
- **Coupons tested** — start and end dates, usage limits, product exclusions. A coupon that stacks with the sale price by accident can wipe out the margin.

### The server

- **Checkout not cached** — page caching makes a store fast, but the cart, checkout and my-account pages must be excluded. A cached cart shows one customer another customer's items.
- **Fresh backup** — files and database, taken right before the sale, from a setup where a restore has been tested.
- **Room to grow** — CPU, memory, and the number of PHP workers. Traffic during a sale can be many times normal. If workers run out, customers see errors instead of slow pages.

### The day itself

- **Updates frozen** — no plugin, theme or WordPress updates on sale day. Update a week before, test, then freeze.
- **Uptime monitor on** — check the checkout page itself, every minute, not just the homepage.
- **Someone on call** — with the hosting provider's and payment gateway's support contacts ready.

## In one line

> **Sale day is not test day.** Every check this week is one less surprise on the day.

**Watch the database live**

```bash
wp db query 'SHOW PROCESSLIST'
```
