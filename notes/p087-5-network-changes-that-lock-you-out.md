---
id: p87
title: "5 network changes that lock you out"
slug: 5-network-changes-that-lock-you-out
sections: [it]
topic: "Networking & DNS"
tags: [Linux, Networking, SysAdmin, Ubuntu, DevOps]
source: "LinkedIn post P87 · Linux series"
linkedin_date: 2027-04-18
design: dontdo
---

# 5 network changes that lock you out

On a remote server, a network mistake does not just break something. It removes your only way to fix it. Five changes that lock admins out, and the safe version of each.

## Quick reference

**1. Don't**

```bash
netplan apply
```

One typo in the new IP, and your SSH session is gone.

**Do instead**

```bash
netplan try
```

Rolls back after 120 seconds unless you confirm.

**2. Don't**

```bash
iptables -F
```

With a DROP policy, flushing the rules blocks everything.

**Do instead**

```bash
iptables -P INPUT ACCEPT && iptables -F
```

Set the policy to ACCEPT first, then flush.

**3. Don't**

```bash
vi /etc/resolv.conf
```

systemd-resolved rewrites it. Your change disappears.

**Do instead**

```bash
resolvectl status
```

See who manages DNS, and change it there.

**4. Don't**

```bash
ip route add 10.8.0.0/24 via 10.0.0.1
```

Works now. Gone after the next reboot.

**Do instead**

routes: in `/etc/netplan/*.yaml`

Put it in the network config so it survives a reboot.

**5. Don't**

```bash
ping db01
```

ICMP is often blocked. No reply does not mean down.

**Do instead**

```bash
nc -zv db01 5432
```

Test the real port that the app uses.

## Explained

1. `netplan apply`
   It applies the new network config immediately. One wrong IP, gateway or interface name, and your SSH session is gone. Instead: `netplan try`. It applies the change and rolls it back automatically after 120 seconds unless you press Enter to confirm.

2. `iptables -F`
   Flushing the rules sounds like "open everything". But if the default policy is DROP, removing the rules that allowed SSH blocks everything, including you. Instead: `iptables -P INPUT` ACCEPT first, then flush.

3. Editing `/etc/resolv.conf` directly
   On most modern distributions, systemd-resolved or NetworkManager manages this file and rewrites it. Your change works for a while, then quietly disappears. Instead: `resolvectl status` shows who is in charge of DNS. Change it there, for example in netplan.

4. ip route add for a permanent route
   It works immediately, so it feels finished. After the next reboot it is gone, and nobody remembers why the VPN subnet stopped working. Instead: add the route to the network configuration, like a routes: section in netplan.

5. ping to test a service
   Many networks block ICMP. No ping reply does not mean the server is down, and a reply does not mean the service works. Instead: `nc -zv db01 5432` tests the actual port the application uses.

> **The rule behind all five:** before any network change on a remote server, have a way back. A rollback timer, a provider console, or a second session open.

## In one line

> **Always have a way back.** A timer, a console or a second session. Before every change.

**The safest network command**

```bash
netplan try --timeout 60
```
