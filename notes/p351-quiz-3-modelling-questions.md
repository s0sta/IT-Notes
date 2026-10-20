---
id: p351
title: "Quiz: 3 modelling questions"
slug: quiz-3-modelling-questions
sections: [it]
topic: "Databases & SQL"
tags: [SQL, DataModelling, DatabaseDesign, PostgreSQL, Backend]
source: "LinkedIn post P351 · Data series"
linkedin_date: 2028-12-24
design: quiz
---

# Quiz: 3 modelling questions

Three questions separate a schema that was designed from one that grew a table at a time. Answer them before the reveal, then check the reasoning.

## Quick reference

**Q1. What does third normal form remove from a table?**

- a) Columns that depend on another non-key column
- b) Every column that is not a primary key
- c) All duplicate rows

> **Answer:** a) Columns that depend on another non-key column. 3NF removes a transitive dependency: a non-key column that depends on another non-key column, such as a city that follows from a postcode.

**Q2. When is denormalising a table the right call?**

- a) After a measured query needs fewer joins
- b) Before launch, to save a join later
- c) Whenever the schema has more than five tables

> **Answer:** a) After a measured query needs fewer joins. Denormalising is a trade, not a default: it removes a join from a read you have timed and adds a write cost and a drift risk you must own.

**Q3. Why does the order of columns in an index matter?**

- a) The leftmost column must match the query
- b) Indexes sort on the last column first
- c) Order only changes the storage size

> **Answer:** a) The leftmost column must match the query. A B-tree sorts by the first column, then the second. A query filtering only on the second column cannot seek the tree, so pick the leftmost column from the query.

## Explained

**The first question**  
What does third normal form remove? A transitive dependency: a non-key column that depends on another non-key column. The postcode determines the city, so a city column in the orders table can disagree with the city column in another row. Third normal form removes the redundancy that lets two rows tell different stories.

**The second question**  
When is denormalising the right call? After a measured query needs fewer joins, and the write cost is understood. Before launch it is a guess, and the guess usually copies the column that changes most often.

**The third question**  
Why does the order of columns in a composite index matter? A B-tree is sorted by the first column, then the second. A query that filters only on the second column cannot seek through the tree, so the leftmost column should be the one your queries use most.

**What they share**  
All three are decisions about where a fact lives and how it is found, not about which database you bought.

> **The honest caveat:** these are defaults, not laws. A reporting table can be denormalised on purpose, and a partial index can beat the textbook column order when it matches the query exactly.

> **The lesson:** model for the facts, index for the queries, and measure both.

## In one line

> **Model for the query you run.** Three answers that decide the schema and the index.

**Check the plan**

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT 1;
```
