---
id: p129
title: "Block vs File vs Object storage"
slug: block-vs-file-vs-object-storage
sections: [it, devsecops]
topic: "Storage & infrastructure"
tags: [Storage, CloudComputing, ITInfrastructure, AWS, SysAdmin]
source: "LinkedIn post P129 · Linux + IT series"
linkedin_date: 2027-07-25
design: matrix
---

# Block vs File vs Object storage

Block, file and object storage are the three building blocks behind almost every server and cloud setup. Choosing the wrong one makes things slow, expensive, or both.

## Quick reference

| | **Block** | **File** | **Object** |
|:--|:--|:--|:--|
| Looks like | A raw disk | Folders and files | Objects in a bucket |
| Accessed by | One server | Many, NFS/SMB | Anyone, HTTPS |
| Examples | EBS, iSCSI | NFS, SMB, EFS | S3, MinIO, Blob |
| Edit in place | ✅ Yes | ✅ Yes | ❌ Replace object |
| Scales to | 🟡 One volume | 🟡 Large | ✅ Near unlimited |
| Best for | Databases, VMs | Shared files | Backups, media |

**How to pick**

- **Block** → databases and VM disks that need low latency.
- **File** → shared folders that people and apps use together.
- **Object** → backups, archives and huge amounts of static data.

## Explained

Block storage looks like a raw disk. The server formats it with a filesystem and mounts it. AWS EBS, an iSCSI LUN from a SAN, and the virtual disk of a VM are all block storage. It gives the lowest latency and lets you change any byte in place, which is exactly what databases need. Usually one server uses one volume at a time.

File storage looks like folders and files, shared over the network with NFS or SMB. Many servers and users can read and write the same files at once. File shares, home directories and AWS EFS are file storage. It is the natural choice for shared team files and applications that expect a normal filesystem path.

Object storage stores whole objects in a bucket, each with a key and metadata, accessed over HTTPS with an API. Amazon S3, MinIO and Azure Blob are object storage. You cannot edit part of an object, you replace it. In exchange, it scales to practically unlimited size, is very durable, and is usually the cheapest per gigabyte.

### How to choose

A database or VM disk: block.  
Folders that several people or servers share: file.  
Backups, archives, logs, images and video, website assets: object. With versioning and object lock, it is also a strong defence against ransomware deleting your backups.

Match the storage to how the data is accessed.

## In one line

> **Match the storage to the access.** How the data is used decides where it should live.

**See your block devices**

```bash
lsblk -f
```
