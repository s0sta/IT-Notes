---
id: p125
title: "Quiz: 3 security questions everyone in IT should answer"
slug: quiz-3-security-questions-everyone-in-it-should-answer
sections: [it]
topic: "Security & hardening"
tags: [CyberSecurity, SecurityAwareness, InfoSec, ITSecurity, Phishing]
source: "LinkedIn post P125 · Linux + IT series"
linkedin_date: 2027-07-15
design: quiz
---

# Quiz: 3 security questions everyone in IT should answer

Three security questions that everyone in IT should be able to answer instantly. They sound simple. Getting them wrong is expensive.

## Quick reference

**Q1. What is the right way to store user passwords in a database?**

- a) Encrypt them with AES
- b) Hash them with SHA-256
- c) Hash them with bcrypt or Argon2

> **Answer:** c) Hash them with bcrypt or Argon2. Slow, salted password hashes make brute force expensive. Fast hashes like SHA-256 are cracked quickly.

**Q2. Your CEO emails asking you to buy gift cards urgently. What first?**

- a) Reply to confirm the amount
- b) Check with the CEO another way
- c) Buy them, it is the CEO

> **Answer:** b) Check with the CEO another way. Call or message the CEO on a known number. Urgency plus an unusual request is the classic sign of fraud.

**Q3. Which of these counts as multi-factor authentication?**

- a) Password + a security question
- b) Password + a code from an app
- c) Two different passwords

> **Answer:** b) Password + a code from an app. MFA needs different types: something you know plus something you have. Two passwords are both know.

## Explained

1. What is the right way to store user passwords in a database?

> **Answer:** hash them with a slow, salted password hashing algorithm like bcrypt or Argon2. Encryption is wrong, because whoever steals the key can decrypt every password. Plain SHA-256 is also wrong, because it is designed to be fast, and modern GPUs can test billions of guesses per second against it. Slow password hashes make every guess expensive, and a unique salt per user stops attackers from cracking everyone at once.

2. Your CEO emails asking you to buy gift cards urgently. What do you do first?

> **Answer:** verify through a different channel. Call or message the CEO on a number you already know, not one from the email. This is business email compromise, and the pattern is always the same: a person with authority, urgency, secrecy, and an unusual request involving money. Real executives are rarely offended by a quick check.

3. **Which of these counts as multi-factor authentication?**

> **Answer:** a password plus a code from an authenticator app. MFA means combining different types of factors: something you know, something you have, or something you are. A password and a security question are both something you know, so that is still a single factor. Two passwords, the same.

None of this needs expensive tools. It needs people who know the basics and use them every day.

## In one line

> **Security is mostly good habits.** The basics stop most real attacks.

**Today's habit:** verify unusual requests on a second channel
