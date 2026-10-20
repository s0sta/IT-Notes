---
id: p331
title: "Quiz: 3 SQL questions"
slug: quiz-3-sql-questions
sections: [it]
topic: "Databases & SQL"
tags: [SQL, PostgreSQL, Databases, QueryPlans, Quiz]
source: "LinkedIn post P331 · Data series"
linkedin_date: 2028-11-07
design: quiz
---

# Quiz: 3 SQL questions

Three SQL questions show up in every interview, and the wrong answer is usually the one that sounds like a rule.

## Quick reference

**Q1. Why can a sequential scan beat an index on a small table?**

- a) The whole table fits in a few pages
- b) Indexes are ignored below 1,000 rows
- c) A sequential scan uses less CPU

> **Answer:** a) The whole table fits in a few pages. An index scan pays a root-to-leaf descent plus a heap fetch per row. When the table fits in a few pages, reading every page once is cheaper; the planner prices both.

**Q2. In a composite index on (a, b), what does the leftmost prefix mean?**

- a) A filter on a, or on a and b, can use it
- b) A filter on b alone can use it
- c) Column order does not matter

> **Answer:** a) A filter on a, or on a and b, can use it. The index is sorted by a, then by b. A filter on b alone cannot seek, because b is only ordered inside each value of a; a range on a also limits the b part.

**Q3. Which isolation level stops a phantom read?**

- a) SERIALIZABLE
- b) READ COMMITTED
- c) READ UNCOMMITTED

> **Answer:** a) SERIALIZABLE. A phantom is a new row in a repeated range query. READ COMMITTED allows it; SERIALIZABLE does not. PostgreSQL's REPEATABLE READ also hides phantoms.

## Explained

**The small table**  
Question one: why can a sequential scan beat an index on a small table? Because the planner compares costs, not rules. An index scan pays for a descent from root to leaf and then a heap fetch per row; when the table fits in a handful of pages, reading all of them sequentially is cheaper. The index is not ignored; it is priced.

**The prefix**  
Question two: in a composite index on (a, b), what does the leftmost prefix mean? The index is sorted by a, then by b. A filter on a, or on a and b, can use it; a filter on b alone cannot seek, because b is only ordered inside each a. A range on a limits how much of b the scan can use.

**The phantom**  
Question three: which isolation level stops a phantom read? A phantom is a row that appears between two reads of the same range. READ COMMITTED allows it; SERIALIZABLE rules it out. PostgreSQL's REPEATABLE READ also hides phantoms because it reads one snapshot, but SERIALIZABLE is the level that rules out every anomaly.

> **The honest caveat:** the planner's choice depends on statistics, cost settings and the correlation of the column, so the same query can flip plans after an ANALYZE or a version upgrade.

> **The lesson:** the planner is always costing; learn what it prices, and the three answers become obvious.

## In one line

> **Read the plan, not the rule.** Three answers that decide how you read a query plan.

**Try it**

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT 1;
```
