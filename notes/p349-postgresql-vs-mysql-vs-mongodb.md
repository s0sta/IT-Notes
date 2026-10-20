---
id: p349
title: "PostgreSQL vs MySQL vs MongoDB"
slug: postgresql-vs-mysql-vs-mongodb
sections: [it]
topic: "Databases & SQL"
tags: [PostgreSQL, MySQL, MongoDB, Databases, DataModelling]
source: "LinkedIn post P349 · Data series"
linkedin_date: 2028-12-19
design: matrix
---

# PostgreSQL vs MySQL vs MongoDB

The schema argument is usually a brand argument, and the brand is rarely the reason the query is slow. Three engines, six rows, and the row that decides the rest is the first one.

## Quick reference

| | **PostgreSQL** | **MySQL** | **MongoDB** |
|:--|:--|:--|:--|
| Data model | Relational, extensible | Relational, InnoDB | Document, BSON |
| Joins | Full SQL joins | Full SQL joins | Limited, via $lookup |
| Transactions | Full ACID, MVCC | ACID on InnoDB | Multi-doc since 4.0 |
| Replication | Streaming, logical | Binlog, group repl | Replica sets |
| Scaling | Read replicas | Read replicas | Sharding built in |
| Best for | Complex queries, GIS | Simple web apps | Flexible documents |

**How to pick**

- **PostgreSQL** → complex queries, strong SQL.
- **MySQL** → simple read-heavy web apps.
- **MongoDB** → flexible documents at scale.

## Explained

**Data model**  
PostgreSQL and MySQL are relational and give you tables, constraints and SQL. MongoDB stores BSON documents, so a record is a tree you read whole rather than a row you join.

**Joins and transactions**  
SQL joins are first class in both relational engines. MongoDB has $lookup, a left outer join in the aggregation pipeline with more limits. PostgreSQL and MySQL on InnoDB give full ACID; MongoDB has multi-document transactions since 4.0 on replica sets, and since 4.2 across shards.

**Replication and scaling**  
PostgreSQL streams WAL and offers logical replication; MySQL uses the binlog and group replication; MongoDB uses replica sets with automatic failover. Both relational engines scale reads with replicas and otherwise want a bigger machine, while MongoDB shards on a key from the start.

**Picking**  
Start with the shape of the data and the queries. Known schema and ad hoc reporting point at PostgreSQL, which is also the strongest on complex queries and GIS; a simple CRUD app with a big read load fits MySQL; documents that change shape per tenant fit MongoDB.

> **The honest caveat:** every engine has moved. MySQL 8 has window functions, PostgreSQL has JSONB, MongoDB has transactions, so the version in front of you matters more than the logo.

> **The lesson:** pick the model the data has, then the engine that runs it best.

## In one line

> **Pick the model the data has.** The engine is a data-shape decision before it is a brand decision.

**See a plan**

```sql
EXPLAIN (FORMAT JSON) SELECT 1;
```
