---
id: p128
title: "Active Directory vs Entra ID"
slug: active-directory-vs-entra-id
sections: [it, devsecops]
topic: "Windows & Active Directory"
tags: [ActiveDirectory, EntraID, Microsoft365, IAM, CloudComputing]
source: "LinkedIn post P128 · Linux + IT series"
linkedin_date: 2027-07-22
design: compare
---

# Active Directory vs Entra ID

Active Directory and Entra ID, formerly Azure AD, share part of a name. They are very different systems, and most companies today use both.

## Quick reference

| | **AD DS** | **ENTRA ID** |
|:--|:--|:--|
| Runs on | Your domain controllers | Microsoft's cloud |
| Protocols | Kerberos, NTLM, LDAP | OAuth 2.0, OIDC, SAML |
| Structure | OUs and Group Policy | Flat, admin units |
| Device policy | Group Policy | Intune |
| Access rules | Network location | Conditional Access |
| Together | Synced with Entra Connect | Hybrid identity |

**AD DS** (On-premises Active Directory): Domain controllers in your network. Kerberos, LDAP and Group Policy.

```powershell
Get-ADUser jsmith
```

**ENTRA ID** (Microsoft cloud identity): Identity for Microsoft 365 and cloud apps. Modern sign-in protocols.

```powershell
Get-MgUser -UserId jsmith
```

- AD DS → on-prem servers, file shares and classic Windows apps.
- Entra ID → Microsoft 365, SaaS apps and modern device management.

## Explained

Active Directory Domain Services runs on domain controllers in your own network. Computers join the domain, users log in with Kerberos, applications query it over LDAP, and Group Policy configures every machine. It has a deep structure of organizational units, and it was designed for a world where everyone worked inside the office network.

Entra ID is Microsoft's cloud identity service. It is what you sign in to for Microsoft 365, and it connects to thousands of SaaS applications using OAuth 2.0, OpenID Connect and SAML. There are no OUs or Group Policy. Devices are managed with Intune, and access is controlled by Conditional Access: who you are, which device, from where, and how risky the sign-in looks.

### How they work together

Most organizations run hybrid identity. Entra Connect, or the newer Cloud Sync, synchronizes users and groups from AD to Entra ID, so people have one account for both the file server and Microsoft 365.

### Where people get confused

Entra ID is not AD in the cloud. You cannot point an old application that needs LDAP or Kerberos at it without extra services.  
Moving to the cloud does not remove AD overnight. File servers, legacy apps and on-premises systems often keep it alive for years.

AD DS for the on-premises world. Entra ID for the cloud. A hybrid bridge between them.
