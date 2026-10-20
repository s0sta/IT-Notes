---
id: p106
title: "NAT vs Port forwarding"
slug: nat-vs-port-forwarding
sections: [it]
topic: "Networking & DNS"
tags: [Networking, CCNA, Firewall, ITInfrastructure, NetworkSecurity]
source: "LinkedIn post P106 · Linux + IT series"
linkedin_date: 2027-06-01
design: compare
---

# NAT vs Port forwarding

NAT and port forwarding are configured in the same router menu, and they are often confused. They work in opposite directions.

## Quick reference

| | **NAT** | **PORT FWD** |
|:--|:--|:--|
| Direction | Outbound, inside to out | Inbound, outside to in |
| Purpose | Share one public IP | Publish one service |
| Who starts it | The inside device | The outside client |
| Default | On, on every router | Off until you add it |
| Risk | Low | Exposes that service |
| Example | Office PCs browsing | A web server on 443 |

**NAT** (Many devices, one public IP): Private devices go out to the internet sharing one public address.

Example: `10.0.0.0/24 -> 203.0.113.5`

**PORT FWD** (Let one service in): Sends traffic for one public port to one server inside.

Example: `203.0.113.5:443 -> 10.0.0.20`

- NAT → lets the inside reach out.
- Port forwarding → lets the outside reach in, one port at a time.

## Explained

NAT, or more precisely source NAT and PAT, lets many private devices share one public IP address. When a PC at 10.0.0.15 opens a website, the router replaces its private address with the public one, 203.0.113.5, and remembers the connection so the reply finds its way back to the right PC. It is on by default on every home and office router, and it only works for connections started from the inside.

Port forwarding, or destination NAT, works the other way. It tells the router: traffic arriving on public port 443 should go to the server at 10.0.0.20. It is off until you add it, because it deliberately lets the outside world reach something inside.

### Where people get confused

"NAT is my firewall." NAT does block unsolicited inbound traffic as a side effect, but it is not a security policy. A real firewall rule set is still needed, and IPv6 usually has no NAT at all.  
"I forwarded the port but it still does not work." Check that the server is listening on that port, that its own firewall allows it, and that the ISP does not use carrier-grade NAT, which means you do not have a real public IP to forward.

The risk is very different. NAT exposes nothing new. Every port forward is a service on the internet that needs patching, monitoring and ideally a reverse proxy or VPN in front.

NAT lets the inside reach out. Port forwarding lets the outside reach in.
