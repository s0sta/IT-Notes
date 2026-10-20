---
id: p151
title: "Data size and speed units, decoded"
slug: data-size-and-speed-units-decoded
sections: [it]
topic: "Networking & DNS"
tags: [Networking, Storage, ITSupport, SysAdmin, DevOps]
source: "LinkedIn post P151 · IT series"
linkedin_date: 2027-09-14
design: numbers
---

# Data size and speed units, decoded

Half of all arguments about "why is it so slow" come down to mixing up units. Six that trip people up constantly.

## Quick reference

| Number | What | Why it matters | |
|:--|:--|:--|:--|
| **1 KB** | vs 1 KiB | KB is 1000 bytes. KiB is 1024. Disks use KB, RAM uses KiB. | kilo |
| **8 bits** | = 1 byte | Networks count bits, storage counts bytes. Divide by 8. | b vs B |
| **100 Mbps** | = 12.5 MB/s | A 100 megabit link moves 12.5 megabytes a second. | link |
| **1 TB** | = 1000 GB | A 1 TB drive shows ~931 GiB in the OS. Same disk, two units. | disk |
| **1 Gbps** | = 125 MB/s | Gigabit ethernet, at best. Real throughput is lower. | LAN |
| **ms vs us** | 1000x apart | A millisecond is a thousand microseconds. Know which one. | time |

## Explained

1 KB vs 1 KiB. A kilobyte (KB) is 1000 bytes. A kibibyte (KiB) is 1024. Storage vendors use the decimal KB, MB, TB; operating systems and RAM use the binary KiB, MiB, GiB. This is why a "1 TB" drive shows up as about 931 GiB. Nothing is missing; they are two different units.

8 bits = 1 byte. The single most useful fact here. Networks are measured in bits per second (lowercase b), storage and files in bytes (uppercase B). To compare them, divide the network number by 8.

100 Mbps = 12.5 MB/s. A 100 megabit internet connection moves at most 12.5 megabytes per second. So a 1 GB download takes around 80 seconds at full speed, not 10. The "slow" download is often just bits-versus-bytes.

1 TB = 1000 GB in marketing, about 931 GiB in the OS. Same disk, two unit systems.

1 Gbps = 125 MB/s. Gigabit ethernet tops out around there, and real-world throughput is lower due to overhead.

ms vs us. A millisecond is a thousand microseconds. An SSD at 100 us and a disk at 10 ms are a hundred times apart. Read the unit before you compare the number.

The one rule to remember: check whether it is bits or bytes. Lowercase b, uppercase B. That alone clears up most confusion.

## In one line

> **Bits or bytes? Always check.** Half of all speed confusion is b versus B.

**The rule:** divide Mbps by 8 for MB/s
