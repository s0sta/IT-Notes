---
id: p334
title: "The MySQL cheat sheet"
slug: the-mysql-cheat-sheet
sections: [it]
topic: "Databases & SQL"
tags: [MySQL, Databases, SQL, DevOps, CheatSheet]
source: "LinkedIn post P334 · Data series"
linkedin_date: 2028-11-14
design: cheatsheet
---

# The MySQL cheat sheet

MySQL sits behind a lot of PHP, WordPress and custom applications, and most of the work happens in the client. Four blocks cover the commands you type when something is slow or locked.

## Quick reference

### Connect

```bash
mysql -u root -p
mysql -h db1 -u app -p shop
mysql --defaults-file=/etc/my.cnf
mysql -e 'SELECT VERSION();'
mysqladmin -u root -p ping
```

### Inspect

```sql
SHOW DATABASES;
SHOW TABLES;
SHOW TABLE STATUS\G
SHOW INDEX FROM orders;
EXPLAIN SELECT * FROM orders;
```

### Users

```sql
SELECT user, host FROM mysql.user;
SHOW GRANTS FOR 'app'@'%';
CREATE USER 'app'@'%';
GRANT SELECT ON shop.* TO 'app'@'%';
REVOKE ALL ON shop.* FROM 'app'@'%';
```

### Replication

```sql
SHOW REPLICA STATUS\G
SHOW REPLICAS;
SHOW BINARY LOGS;
START REPLICA;
STOP REPLICA;
```

## Explained

**Connect**  
`mysql -u root -p` prompts for a password instead of putting it in your shell history. `mysql -h db1 -u app -p shop` names host, user and database in one line. `mysql --defaults-file=/etc/my.cnf` reads a client file, `mysql -e` runs one statement and exits, and `mysqladmin -u root -p ping` answers whether the server is alive.

**Inspect**  
SHOW DATABASES and SHOW TABLES answer the first two questions. `SHOW TABLE STATUS\G` gives engine, collation, row estimate and data length. SHOW INDEX FROM orders shows the indexes and their cardinality, and EXPLAIN SELECT \* FROM orders shows the plan the optimiser chose.

**Users**  
SELECT user, host FROM mysql.user lists the accounts. SHOW GRANTS FOR 'app'@'%' shows what one account can do, CREATE USER 'app'@'%' makes an account, and GRANT and REVOKE change its rights on the shop schema. Account and host are one identity: 'app'@'localhost' is not 'app'@'%'.

**Replication**  
`SHOW REPLICA STATUS\G` reads the replica, SHOW REPLICAS lists replicas on the source, and SHOW BINARY LOGS shows the files a replica needs. START REPLICA and STOP REPLICA start and stop replication.

> **The honest caveat:** most of the replica block uses the 8.0.22 names; on 5.7 their equivalents say SLAVE, and SHOW TABLE STATUS row counts are estimates for InnoDB.

> **The lesson:** know which account you are, which plan you have, and whether the replica is behind.

## In one line

> **Know the plan before the query.** The client is the shortest path to the answer.

**See the plan**

```sql
EXPLAIN SELECT * FROM orders;
```
