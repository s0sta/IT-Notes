---
id: p117
title: "Hashing vs Encryption"
slug: hashing-vs-encryption
sections: [it, devsecops]
topic: "Security & hardening"
tags: [CyberSecurity, Cryptography, InfoSec, ITSecurity, WebSecurity]
source: "LinkedIn post P117 · Linux + IT series"
linkedin_date: 2027-06-27
design: compare
---

# Hashing vs Encryption

Hashing and encryption are both called scrambling data, and mixing them up leads to real security mistakes.

## Quick reference

| | **HASHING** | **ENCRYPTION** |
|:--|:--|:--|
| Reversible | No | Yes, with the key |
| Output size | Fixed (256 bits) | About the input size |
| Key needed | No | Yes |
| Used for | Integrity, passwords | Privacy of data |
| Examples | SHA-256, bcrypt | AES, RSA, TLS |
| Passwords | Yes, slow and salted | Never |

**HASHING** (One way, no key): Turns any data into a fixed fingerprint. It cannot be turned back.

```bash
sha256sum backup.tar.gz
```

**ENCRYPTION** (Two way, with a key): Locks data so only someone with the key can read it again.

```bash
gpg -c backup.tar.gz
```

- Hashing → prove data has not changed, store passwords.
- Encryption → keep data secret, and get it back later.

## Explained

Hashing is one way. sha256sum backup.tar.gz turns a file of any size into a fixed 256-bit fingerprint. The same input always gives the same hash, and changing a single byte changes it completely. There is no key, and no way to turn the hash back into the original.

Encryption is two way. `gpg -c backup.tar.gz` locks the file with a key or passphrase. Anyone with the key can decrypt it and get the original data back. Without the key, it is unreadable.

### Where each one belongs

Integrity: publish the SHA-256 hash of a download or a backup. Anyone can check the file has not been changed or corrupted.  
Privacy: encrypt backups before they leave the server, disks with BitLocker or LUKS, and traffic with TLS. The data must be readable again later, so it has to be encryption.  
Passwords: hash them, never encrypt them. If passwords are encrypted, whoever steals the key gets every password. But use a slow, salted password hash like bcrypt or Argon2, not plain SHA-256, which is fast enough to brute force billions of guesses.

A quick test: do you ever need the original data back? Then you need encryption. Do you only need to check that something matches? Then you need a hash.

Hashing proves. Encryption hides.
