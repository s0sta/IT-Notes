---
id: p347
title: "The N+1 query problem, drawn"
slug: the-n-1-query-problem-drawn
sections: [it]
topic: "Databases & SQL"
tags: [Databases, ORM, Backend, Performance, SQL]
source: "LinkedIn post P347 · Data series"
linkedin_date: 2028-12-14
design: explainer
---

# The N+1 query problem, drawn

The page takes four seconds and the database reports a hundred and one queries, each one fast. That gap is the N+1 problem, and it is easier to see in a count than a profile.

## Quick reference

### The loop

- One query for the list, one per row
- A hundred orders mean a hundred and one trips
- Each trip pays latency, not CPU
- Nothing in the loop looks expensive

### The ORM

- Lazy loading fetches on first access
- It looks like a property, it costs a query
- The loop hides it in plain sight
- Turn on statement logging and watch

### The fix

- Load the relation with the first query
- A join, or a second query with IN
- Batch the ids, keep one round trip
- Then the loop touches memory only

### The measurement

- Count queries per request, not seconds
- Log every statement in development
- Assert the count in a test
- A budget of five catches the next one

> **Note:** Seconds move with the machine. The query count does not.

## Explained

**The loop**  
The code loads a hundred orders, then loops over them and asks each order for its customer. One query for the list and one per row: a hundred and one round trips. Each trip is short, the latency between them is not, and a remote database turns milliseconds into seconds.

**The ORM**  
Lazy loading makes the association look like a property. Writing order.customer reads like a field and costs a query the first time it is touched. Nothing in the loop mentions a query, which is why a code review walks past it and a fast local database hides it.

**The fix**  
Load the relation with the first query: a join, or a second query that fetches every customer with WHERE id IN. Two queries, one round trip each, and the loop then touches memory. The second often wins because it keeps the row count honest.

**The measurement**  
Count statements per request. Log every statement in development, add a counter around the request, and assert the count in a test. Seconds move with the machine; the count does not.

> **The honest caveat:** eager loading everything turns a small N+1 into one large join with duplicated rows. Measure the query count and the row count before you call it fixed.

> **The lesson:** N+1 is a loop you can see once you count the queries.

## In one line

> **Count the queries, not the seconds.** A hundred and one round trips is the bug, and it is measurable.

**Log every query**

```sql
SET log_statement = 'all';
```
