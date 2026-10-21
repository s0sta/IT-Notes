<a href="https://s0sta.com"><img src=".github/assets/banner.png" alt="s0sta IT notes: commands and checklists you can copy and run" width="100%"></a>

# IT notes

Practical IT notes from my LinkedIn posts: Linux, Windows, networks and DNS, storage, web servers, databases, Bash and Python checks, security and incident response. Every note has a **quick reference** you can copy, the **full explanation**, and the **script** when there is one.

| Notes | Topics | Scripts |
|:--|:--|:--|
| **271** | **14** | **84** (64 Python + 20 Bash), no extra packages |

Cloud, containers, Kubernetes, CI/CD and security automation are in **[DevSecOps-Notes](https://github.com/s0sta/DevSecOps-Notes)**. The 194 notes that fit both are in both repos.

## How to use it

1. Open a topic below and pick a note.
2. Copy a command from a code box. GitHub shows a copy button on every box.
3. Need a script? It is at the end of the note and in [`scripts/`](scripts).

Looking for one command? Use the search box at the top of GitHub, for example `lvextend` or `journalctl`.

## Notes by topic

<details>
<summary><b>Python scripts</b> · 64 notes</summary>

- [A disk-space alert in 15 lines of Python](notes/p172-a-disk-space-alert-in-15-lines-of-python.md) <sub>P172 · script</sub>
- [Find risky file permissions with Python](notes/p177-find-risky-file-permissions-with-python.md) <sub>P177 · script</sub>
- [A TLS certificate expiry checker in Python](notes/p182-a-tls-certificate-expiry-checker-in-python.md) <sub>P182 · script</sub>
- [A website uptime and latency checker in Python](notes/p187-a-website-uptime-and-latency-checker-in-python.md) <sub>P187 · script</sub>
- [A self-cleaning backup script in Python](notes/p192-a-self-cleaning-backup-script-in-python.md) <sub>P192 · script</sub>
- [A systemd service watchdog in Python](notes/p207-a-systemd-service-watchdog-in-python.md) <sub>P207 · script</sub>
- [Find SSH brute-force attempts with Python](notes/p212-find-ssh-brute-force-attempts-with-python.md) <sub>P212 · script</sub>
- [Check a site's security headers with Python](notes/p217-check-a-sites-security-headers-with-python.md) <sub>P217 · script</sub>
- [An HTTP redirect chain checker in Python](notes/p280-an-http-redirect-chain-checker-in-python.md) <sub>P280 · script</sub>
- [An SSH configuration auditor in Python](notes/p305-an-ssh-configuration-auditor-in-python.md) <sub>P305 · script</sub>
- [A query plan differ in Python](notes/p325-a-query-plan-differ-in-python.md) <sub>P325 · script</sub>
- [A slow-query log report in Python](notes/p330-a-slow-query-log-report-in-python.md) <sub>P330 · script</sub>
- [A backup verifier in Python](notes/p335-a-backup-verifier-in-python.md) <sub>P335 · script</sub>
- [A table bloat report in Python](notes/p340-a-table-bloat-report-in-python.md) <sub>P340 · script</sub>
- [An index advisor in Python](notes/p345-an-index-advisor-in-python.md) <sub>P345 · script</sub>
- [A table size report in Python](notes/p350-a-table-size-report-in-python.md) <sub>P350 · script</sub>
- [HTTP timing phases in Python](notes/p474-http-timing-phases-in-python.md) <sub>P474 · script</sub>
- [A TLS inspector in Python](notes/p475-a-tls-inspector-in-python.md) <sub>P475 · script</sub>
- [A DNS check in Python](notes/p485-a-dns-check-in-python.md) <sub>P485 · script</sub>
- [A TCP port check in Python](notes/p486-a-tcp-port-check-in-python.md) <sub>P486 · script</sub>
- [A latency matrix in Python](notes/p506-a-latency-matrix-in-python.md) <sub>P506 · script</sub>
- [An MTU calculator in Python](notes/p515-an-mtu-calculator-in-python.md) <sub>P515 · script</sub>
- [A bandwidth-delay product in Python](notes/p516-a-bandwidth-delay-product-in-python.md) <sub>P516 · script</sub>
- [An sshd_config audit in Python](notes/p525-an-sshd-config-audit-in-python.md) <sub>P525 · script</sub>
- [A sudoers audit in Python](notes/p526-a-sudoers-audit-in-python.md) <sub>P526 · script</sub>
- [A systemd hardening score in Python](notes/p529-a-systemd-hardening-score-in-python.md) <sub>P529 · script</sub>
- [A cron audit in Python](notes/p530-a-cron-audit-in-python.md) <sub>P530 · script</sub>
- [An inode exhaustion forecaster](notes/p572-an-inode-exhaustion-forecaster.md) <sub>P572 · script</sub>
- [An OOM kill report](notes/p573-an-oom-kill-report.md) <sub>P573 · script</sub>
- [A zombie process scan](notes/p574-a-zombie-process-scan.md) <sub>P574 · script</sub>
- [A log flood detector](notes/p575-a-log-flood-detector.md) <sub>P575 · script</sub>
- [A file descriptor leak finder](notes/p576-a-file-descriptor-leak-finder.md) <sub>P576 · script</sub>
- [A certificate bundle check in Python](notes/p582-a-certificate-bundle-check-in-python.md) <sub>P582 · script</sub>
- [An offboarding access audit in Python](notes/p584-an-offboarding-access-audit-in-python.md) <sub>P584 · script</sub>
- [A password age audit in Python](notes/p585-a-password-age-audit-in-python.md) <sub>P585 · script</sub>
- [A sudo drift report in Python](notes/p586-a-sudo-drift-report-in-python.md) <sub>P586 · script</sub>
- [A restore drill in Python](notes/p612-a-restore-drill-in-python.md) <sub>P612 · script</sub>
- [A table growth report in Python](notes/p613-a-table-growth-report-in-python.md) <sub>P613 · script</sub>
- [A log retention audit in Python](notes/p615-a-log-retention-audit-in-python.md) <sub>P615 · script</sub>
- [An alert dedupe report](notes/p672-an-alert-dedupe-report.md) <sub>P672 · script</sub>
- [A merged incident timeline](notes/p673-a-merged-incident-timeline.md) <sub>P673 · script</sub>
- [A service blast radius report](notes/p674-a-service-blast-radius-report.md) <sub>P674 · script</sub>
- [A severity policy check](notes/p675-a-severity-policy-check.md) <sub>P675 · script</sub>
- [An on-call handoff brief](notes/p676-an-on-call-handoff-brief.md) <sub>P676 · script</sub>
- [A host quarantine plan that keeps the console](notes/p682-a-host-quarantine-plan-that-keeps-the-console.md) <sub>P682 · script</sub>
- [An ordered account lockout plan](notes/p683-an-ordered-account-lockout-plan.md) <sub>P683 · script</sub>
- [A token revocation list, oldest first](notes/p684-a-token-revocation-list-oldest-first.md) <sub>P684 · script</sub>
- [An edge block that checks the allow list](notes/p685-an-edge-block-that-checks-the-allow-list.md) <sub>P685 · script</sub>
- [A kill-switch audit ranked by blast radius](notes/p686-a-kill-switch-audit-ranked-by-blast-radius.md) <sub>P686 · script</sub>
- [A credential rotation planner](notes/p692-a-credential-rotation-planner.md) <sub>P692 · script</sub>
- [A config rollback planner](notes/p693-a-config-rollback-planner.md) <sub>P693 · script</sub>
- [A certificate replacement planner](notes/p694-a-certificate-replacement-planner.md) <sub>P694 · script</sub>
- [A restore point picker](notes/p695-a-restore-point-picker.md) <sub>P695 · script</sub>
- [A node drain simulator](notes/p696-a-node-drain-simulator.md) <sub>P696 · script</sub>
- [An evidence bundle](notes/p702-an-evidence-bundle.md) <sub>P702 · script</sub>
- [A status page draft](notes/p703-a-status-page-draft.md) <sub>P703 · script</sub>
- [A timeline export](notes/p704-a-timeline-export.md) <sub>P704 · script</sub>
- [An action item tracker](notes/p705-an-action-item-tracker.md) <sub>P705 · script</sub>
- [A notification log](notes/p706-a-notification-log.md) <sub>P706 · script</sub>
- [The detection that was never written](notes/p712-the-detection-that-was-never-written.md) <sub>P712 · script</sub>
- [Runbooks that rotted](notes/p713-runbooks-that-rotted.md) <sub>P713 · script</sub>
- [Alerts nobody acts on](notes/p714-alerts-nobody-acts-on.md) <sub>P714 · script</sub>
- [The incident that keeps coming back](notes/p715-the-incident-that-keeps-coming-back.md) <sub>P715 · script</sub>
- [The control you think is on](notes/p716-the-control-you-think-is-on.md) <sub>P716 · script</sub>

</details>

<details>
<summary><b>Networking &amp; DNS</b> · 36 notes</summary>

- [5 network changes that lock you out](notes/p087-5-network-changes-that-lock-you-out.md) <sub>P87</sub>
- [6 port numbers every IT person should know](notes/p094-6-port-numbers-every-it-person-should-know.md) <sub>P94</sub>
- [VLAN vs Subnet](notes/p095-vlan-vs-subnet.md) <sub>P95</sub>
- [9 dig commands for DNS problems](notes/p097-9-dig-commands-for-dns-problems.md) <sub>P97</sub>
- [How an email gets from sender to inbox](notes/p101-how-an-email-gets-from-sender-to-inbox.md) <sub>P101</sub>
- [Quiz: 3 networking questions from IT interviews](notes/p103-quiz-3-networking-questions-from-it-interviews.md) <sub>P103</sub>
- [NAT vs Port forwarding](notes/p106-nat-vs-port-forwarding.md) <sub>P106</sub>
- [Subnet sizes cheat sheet](notes/p127-subnet-sizes-cheat-sheet.md) <sub>P127</sub>
- [How your data is wrapped to cross the network (TCP/IP)](notes/p131-how-your-data-is-wrapped-to-cross-the-network-tcp-ip.md) <sub>P131</sub>
- [Data size and speed units, decoded](notes/p151-data-size-and-speed-units-decoded.md) <sub>P151</sub>
- [The OSI model, grouped](notes/p276-the-osi-model-grouped.md) <sub>P276</sub>
- [TCP vs UDP](notes/p279-tcp-vs-udp.md) <sub>P279</sub>
- [Quiz: 3 infrastructure questions](notes/p281-quiz-3-infrastructure-questions.md) <sub>P281</sub>
- [The TCP handshake in four panels](notes/p472-the-tcp-handshake-in-four-panels.md) <sub>P472</sub>
- [The network debugging cheat sheet](notes/p473-the-network-debugging-cheat-sheet.md) <sub>P473</sub>
- [The edge path](notes/p477-the-edge-path.md) <sub>P477</sub>
- [Anatomy of a connection tuple](notes/p478-anatomy-of-a-connection-tuple.md) <sub>P478</sub>
- [The life of a TCP connection](notes/p479-the-life-of-a-tcp-connection.md) <sub>P479</sub>
- [Quiz: 3 packet questions](notes/p480-quiz-3-packet-questions.md) <sub>P480</sub>
- [5 network mistakes](notes/p481-5-network-mistakes.md) <sub>P481</sub>
- [How DNS resolves a name](notes/p482-how-dns-resolves-a-name.md) <sub>P482</sub>
- [The DNS records cheat sheet](notes/p483-the-dns-records-cheat-sheet.md) <sub>P483</sub>
- [DNS TTL and failover](notes/p484-dns-ttl-and-failover.md) <sub>P484</sub>
- [IPv4 vs IPv6](notes/p487-ipv4-vs-ipv6.md) <sub>P487</sub>
- [Anatomy of a DNS record](notes/p488-anatomy-of-a-dns-record.md) <sub>P488</sub>
- [DNS health at a glance](notes/p489-dns-health-at-a-glance.md) <sub>P489</sub>
- [Quiz: 3 DNS questions](notes/p490-quiz-3-dns-questions.md) <sub>P490</sub>
- [DNS terms, decoded](notes/p491-dns-terms-decoded.md) <sub>P491</sub>
- [The network observability path, drawn](notes/p512-the-network-observability-path-drawn.md) <sub>P512</sub>
- [The packet capture cheat sheet](notes/p513-the-packet-capture-cheat-sheet.md) <sub>P513</sub>
- [Latency, bandwidth and throughput, drawn](notes/p514-latency-bandwidth-and-throughput-drawn.md) <sub>P514</sub>
- [6 network numbers](notes/p517-6-network-numbers.md) <sub>P517</sub>
- [Network health at a glance](notes/p518-network-health-at-a-glance.md) <sub>P518</sub>
- [Anatomy of a network incident](notes/p519-anatomy-of-a-network-incident.md) <sub>P519</sub>
- [Quiz: 3 network operations questions](notes/p520-quiz-3-network-operations-questions.md) <sub>P520</sub>
- [Network terms, decoded](notes/p521-network-terms-decoded.md) <sub>P521</sub>

</details>

<details>
<summary><b>Linux</b> · 31 notes</summary>

- [9 checks after every Linux reboot](notes/p073-9-checks-after-every-linux-reboot.md) <sub>P73</sub>
- [What happens when you press Enter in the shell](notes/p074-what-happens-when-you-press-enter-in-the-shell.md) <sub>P74</sub>
- [5 commands that take servers down](notes/p075-5-commands-that-take-servers-down.md) <sub>P75</sub>
- [9 apt and dpkg commands every Ubuntu admin uses](notes/p076-9-apt-and-dpkg-commands-every-ubuntu-admin-uses.md) <sub>P76</sub>
- [9 checks before you patch a production server](notes/p077-9-checks-before-you-patch-a-production-server.md) <sub>P77</sub>
- [How Linux boots, step by step](notes/p078-how-linux-boots-step-by-step.md) <sub>P78</sub>
- [5 Bash script mistakes that bite in production](notes/p079-5-bash-script-mistakes-that-bite-in-production.md) <sub>P79</sub>
- [9 tar and compression commands](notes/p080-9-tar-and-compression-commands.md) <sub>P80</sub>
- [9 commands to know any server in 60 seconds](notes/p088-9-commands-to-know-any-server-in-60-seconds.md) <sub>P88</sub>
- [The life of a log line](notes/p090-the-life-of-a-log-line.md) <sub>P90</sub>
- [Quiz: 3 Linux questions most admins get wrong](notes/p092-quiz-3-linux-questions-most-admins-get-wrong.md) <sub>P92</sub>
- [6 numbers every sysadmin should know](notes/p105-6-numbers-every-sysadmin-should-know.md) <sub>P105</sub>
- [Ubuntu LTS vs Debian vs Rocky Linux for servers](notes/p107-ubuntu-lts-vs-debian-vs-rocky-linux-for-servers.md) <sub>P107</sub>
- [What a healthy Linux server looks like](notes/p135-what-a-healthy-linux-server-looks-like.md) <sub>P135</sub>
- [9 jq commands for working with JSON](notes/p140-9-jq-commands-for-working-with-json.md) <sub>P140</sub>
- [9 SELinux commands that fix Permission denied](notes/p173-9-selinux-commands-that-fix-permission-denied.md) <sub>P173</sub>
- [Fix: the app works with SELinux off, fails with it on](notes/p176-fix-the-app-works-with-selinux-off-fails-with-it-on.md) <sub>P176</sub>
- [The layers that decide who can touch a file on RHEL](notes/p180-the-layers-that-decide-who-can-touch-a-file-on-rhel.md) <sub>P180</sub>
- [Quiz: 3 RHCSA questions](notes/p181-quiz-3-rhcsa-questions.md) <sub>P181</sub>
- [The Linux command cheat sheet](notes/p274-the-linux-command-cheat-sheet.md) <sub>P274</sub>
- [First-response commands for a host incident](notes/p578-first-response-commands-for-a-host-incident.md) <sub>P578</sub>
- [Four host failure modes](notes/p579-four-host-failure-modes.md) <sub>P579</sub>
- [Quiz: 3 host incident questions](notes/p581-quiz-3-host-incident-questions.md) <sub>P581</sub>
- [The host triage flow](notes/p627-the-host-triage-flow.md) <sub>P627</sub>
- [Bash one-liners for host triage](notes/p628-bash-one-liners-for-host-triage.md) <sub>P628</sub>
- [Four host signals](notes/p629-four-host-signals.md) <sub>P629</sub>
- [9 shell commands for a host checkup](notes/p630-9-shell-commands-for-a-host-checkup.md) <sub>P630</sub>
- [Quiz: 3 host questions](notes/p631-quiz-3-host-questions.md) <sub>P631</sub>
- [Cron and systemd automation commands](notes/p668-cron-and-systemd-automation-commands.md) <sub>P668</sub>
- [5 shell scripting mistakes](notes/p670-5-shell-scripting-mistakes.md) <sub>P670</sub>
- [Quiz: 3 automation questions](notes/p671-quiz-3-automation-questions-2.md) <sub>P671</sub>

</details>

<details>
<summary><b>Databases &amp; SQL</b> · 26 notes</summary>

- [Fix: MySQL Too many connections](notes/p121-fix-mysql-too-many-connections.md) <sub>P121</sub>
- [A zero-downtime database migration](notes/p168-a-zero-downtime-database-migration.md) <sub>P168</sub>
- [How a SQL query runs, drawn](notes/p322-how-a-sql-query-runs-drawn.md) <sub>P322</sub>
- [The four joins, drawn](notes/p323-the-four-joins-drawn.md) <sub>P323</sub>
- [The SQL cheat sheet](notes/p324-the-sql-cheat-sheet.md) <sub>P324</sub>
- [ACID, in four panels](notes/p326-acid-in-four-panels.md) <sub>P326</sub>
- [The B-tree behind your index, drawn](notes/p327-the-b-tree-behind-your-index-drawn.md) <sub>P327</sub>
- [The psql cheat sheet](notes/p328-the-psql-cheat-sheet.md) <sub>P328</sub>
- [OLTP vs OLAP](notes/p329-oltp-vs-olap.md) <sub>P329</sub>
- [Quiz: 3 SQL questions](notes/p331-quiz-3-sql-questions.md) <sub>P331</sub>
- [PostgreSQL architecture, drawn](notes/p332-postgresql-architecture-drawn.md) <sub>P332</sub>
- [Backups: physical, logical, PITR and the restore test](notes/p333-backups-physical-logical-pitr-and-the-restore-test.md) <sub>P333</sub>
- [The MySQL cheat sheet](notes/p334-the-mysql-cheat-sheet.md) <sub>P334</sub>
- [Replication topologies, drawn](notes/p336-replication-topologies-drawn.md) <sub>P336</sub>
- [Isolation levels and the anomalies they stop](notes/p337-isolation-levels-and-the-anomalies-they-stop.md) <sub>P337</sub>
- [The Redis cheat sheet](notes/p338-the-redis-cheat-sheet.md) <sub>P338</sub>
- [5 database mistakes and the fix for each](notes/p339-5-database-mistakes-and-the-fix-for-each.md) <sub>P339</sub>
- [Quiz: 3 database operations questions](notes/p341-quiz-3-database-operations-questions.md) <sub>P341</sub>
- [A read path with a cache, drawn](notes/p342-a-read-path-with-a-cache-drawn.md) <sub>P342</sub>
- [Normalisation in four panels](notes/p343-normalisation-in-four-panels.md) <sub>P343</sub>
- [The EXPLAIN cheat sheet](notes/p344-the-explain-cheat-sheet.md) <sub>P344</sub>
- [Partitioning a big table, drawn](notes/p346-partitioning-a-big-table-drawn.md) <sub>P346</sub>
- [The N+1 query problem, drawn](notes/p347-the-n-1-query-problem-drawn.md) <sub>P347</sub>
- [The psql performance cheat sheet](notes/p348-the-psql-performance-cheat-sheet.md) <sub>P348</sub>
- [PostgreSQL vs MySQL vs MongoDB](notes/p349-postgresql-vs-mysql-vs-mongodb.md) <sub>P349</sub>
- [Quiz: 3 modelling questions](notes/p351-quiz-3-modelling-questions.md) <sub>P351</sub>

</details>

<details>
<summary><b>Security &amp; hardening</b> · 26 notes</summary>

- [9 firewall checks with ufw](notes/p081-9-firewall-checks-with-ufw.md) <sub>P81</sub>
- [Defense in depth: 6 layers of security](notes/p098-defense-in-depth-6-layers-of-security.md) <sub>P98</sub>
- [How a ransomware attack unfolds, and where to stop it](notes/p112-how-a-ransomware-attack-unfolds-and-where-to-stop-it.md) <sub>P112</sub>
- [Hashing vs Encryption](notes/p117-hashing-vs-encryption.md) <sub>P117</sub>
- [9 nmap commands to check your own network](notes/p119-9-nmap-commands-to-check-your-own-network.md) <sub>P119</sub>
- [5 password and access mistakes](notes/p124-5-password-and-access-mistakes.md) <sub>P124</sub>
- [Quiz: 3 security questions everyone in IT should answer](notes/p125-quiz-3-security-questions-everyone-in-it-should-answer.md) <sub>P125</sub>
- [9 checks to harden a fresh RHEL server](notes/p178-9-checks-to-harden-a-fresh-rhel-server.md) <sub>P178</sub>
- [firewalld vs iptables](notes/p179-firewalld-vs-iptables.md) <sub>P179</sub>
- [Zero-trust architecture, drawn](notes/p302-zero-trust-architecture-drawn.md) <sub>P302</sub>
- [The security command cheat sheet](notes/p304-the-security-command-cheat-sheet.md) <sub>P304</sub>
- [The certificate lifecycle](notes/p587-the-certificate-lifecycle.md) <sub>P587</sub>
- [The certificate and key cheat sheet](notes/p588-the-certificate-and-key-cheat-sheet.md) <sub>P588</sub>
- [Four identity failures](notes/p589-four-identity-failures.md) <sub>P589</sub>
- [9 checks before an access review](notes/p590-9-checks-before-an-access-review.md) <sub>P590</sub>
- [Quiz: 3 access questions](notes/p591-quiz-3-access-questions.md) <sub>P591</sub>
- [The config and crypto sweep](notes/p637-the-config-and-crypto-sweep.md) <sub>P637</sub>
- [The openssl shell cheat sheet](notes/p638-the-openssl-shell-cheat-sheet.md) <sub>P638</sub>
- [Four config and crypto failures](notes/p639-four-config-and-crypto-failures.md) <sub>P639</sub>
- [9 steps of a config audit](notes/p640-9-steps-of-a-config-audit.md) <sub>P640</sub>
- [Quiz: 3 config questions](notes/p641-quiz-3-config-questions.md) <sub>P641</sub>
- [The security sweep](notes/p657-the-security-sweep.md) <sub>P657</sub>
- [Security shell commands](notes/p658-security-shell-commands.md) <sub>P658</sub>
- [Four security regressions](notes/p659-four-security-regressions.md) <sub>P659</sub>
- [Bash script vs security tool](notes/p660-bash-script-vs-security-tool.md) <sub>P660</sub>
- [Quiz: 3 security questions](notes/p661-quiz-3-security-questions-2.md) <sub>P661</sub>

</details>

<details>
<summary><b>Incident response &amp; detection</b> · 25 notes</summary>

- [The incident triage pipeline](notes/p677-the-incident-triage-pipeline.md) <sub>P677</sub>
- [Triage commands for the first ten minutes](notes/p678-triage-commands-for-the-first-ten-minutes.md) <sub>P678</sub>
- [Four triage mistakes](notes/p679-four-triage-mistakes.md) <sub>P679</sub>
- [9 steps from alert to incident](notes/p680-9-steps-from-alert-to-incident.md) <sub>P680</sub>
- [Quiz: 3 triage questions](notes/p681-quiz-3-triage-questions.md) <sub>P681</sub>
- [The containment tree](notes/p687-the-containment-tree.md) <sub>P687</sub>
- [Containment commands](notes/p688-containment-commands.md) <sub>P688</sub>
- [Four containment failures](notes/p689-four-containment-failures.md) <sub>P689</sub>
- [9 commands to contain a host](notes/p690-9-commands-to-contain-a-host.md) <sub>P690</sub>
- [Quiz: 3 containment questions](notes/p691-quiz-3-containment-questions.md) <sub>P691</sub>
- [The recovery path, drawn](notes/p697-the-recovery-path-drawn.md) <sub>P697</sub>
- [Recovery command cheat sheet](notes/p698-recovery-command-cheat-sheet.md) <sub>P698</sub>
- [Four recovery failures, explained](notes/p699-four-recovery-failures-explained.md) <sub>P699</sub>
- [9 checks before you call it recovered](notes/p700-9-checks-before-you-call-it-recovered.md) <sub>P700</sub>
- [Quiz: 3 recovery questions](notes/p701-quiz-3-recovery-questions.md) <sub>P701</sub>
- [The evidence path](notes/p707-the-evidence-path.md) <sub>P707</sub>
- [The evidence command sheet](notes/p708-the-evidence-command-sheet.md) <sub>P708</sub>
- [Four evidence failures](notes/p709-four-evidence-failures.md) <sub>P709</sub>
- [Status update by phase](notes/p710-status-update-by-phase.md) <sub>P710</sub>
- [Quiz: 3 evidence questions](notes/p711-quiz-3-evidence-questions.md) <sub>P711</sub>
- [The learning loop](notes/p717-the-learning-loop.md) <sub>P717</sub>
- [Post-incident commands](notes/p718-post-incident-commands.md) <sub>P718</sub>
- [Four learning failures](notes/p719-four-learning-failures.md) <sub>P719</sub>
- [5 postmortem mistakes](notes/p720-5-postmortem-mistakes-2.md) <sub>P720</sub>
- [Quiz: 3 learning questions](notes/p721-quiz-3-learning-questions.md) <sub>P721</sub>

</details>

<details>
<summary><b>Shell scripts</b> · 20 notes</summary>

- [Logs that never rotate](notes/p622-logs-that-never-rotate.md) <sub>P622 · script</sub>
- [Accounts hiding in plain sight](notes/p623-accounts-hiding-in-plain-sight.md) <sub>P623 · script</sub>
- [Ports nobody remembers opening](notes/p624-ports-nobody-remembers-opening.md) <sub>P624 · script</sub>
- [Services that died quietly](notes/p625-services-that-died-quietly.md) <sub>P625 · script</sub>
- [Packages that changed without a deploy](notes/p626-packages-that-changed-without-a-deploy.md) <sub>P626 · script</sub>
- [Config that drifted overnight](notes/p632-config-that-drifted-overnight.md) <sub>P632 · script</sub>
- [SSH keys you forgot about](notes/p633-ssh-keys-you-forgot-about.md) <sub>P633 · script</sub>
- [TLS that is still offering 1.0](notes/p634-tls-that-is-still-offering-1-0.md) <sub>P634 · script</sub>
- [Files that changed under you](notes/p635-files-that-changed-under-you.md) <sub>P635 · script</sub>
- [Certificates before they expire](notes/p636-certificates-before-they-expire.md) <sub>P636 · script</sub>
- [SUID binaries that appeared overnight](notes/p652-suid-binaries-that-appeared-overnight.md) <sub>P652 · script</sub>
- [Secrets in crontabs and env files](notes/p653-secrets-in-crontabs-and-env-files.md) <sub>P653 · script</sub>
- [An image gate for the registry](notes/p654-an-image-gate-for-the-registry.md) <sub>P654 · script</sub>
- [Logins that do not look right](notes/p655-logins-that-do-not-look-right.md) <sub>P655 · script</sub>
- [ACLs that override your permissions](notes/p656-acls-that-override-your-permissions.md) <sub>P656 · script</sub>
- [Retention that never ran](notes/p662-retention-that-never-ran.md) <sub>P662 · script</sub>
- [A backup that copied nothing](notes/p663-a-backup-that-copied-nothing.md) <sub>P663 · script</sub>
- [The cron job that overlapped](notes/p664-the-cron-job-that-overlapped.md) <sub>P664 · script</sub>
- [Renewed certificate, old process](notes/p665-renewed-certificate-old-process.md) <sub>P665 · script</sub>
- [The disk nobody will clean](notes/p666-the-disk-nobody-will-clean.md) <sub>P666 · script</sub>

</details>

<details>
<summary><b>Web servers, TLS &amp; HTTP</b> · 11 notes</summary>

- [9 curl commands for debugging websites](notes/p072-9-curl-commands-for-debugging-websites.md) <sub>P72</sub>
- [How a request reaches your app through nginx](notes/p082-how-a-request-reaches-your-app-through-nginx.md) <sub>P82</sub>
- [9 openssl commands for SSL certificate problems](notes/p084-9-openssl-commands-for-ssl-certificate-problems.md) <sub>P84</sub>
- [Fix: 502 Bad Gateway](notes/p099-fix-502-bad-gateway.md) <sub>P99</sub>
- [9 nginx settings worth knowing](notes/p104-9-nginx-settings-worth-knowing.md) <sub>P104</sub>
- [9 WooCommerce checks before a big sale](notes/p111-9-woocommerce-checks-before-a-big-sale.md) <sub>P111</sub>
- [The stack behind a WordPress / WooCommerce store](notes/p120-the-stack-behind-a-wordpress-woocommerce-store.md) <sub>P120</sub>
- [How a Let's Encrypt certificate is issued and renewed](notes/p123-how-a-lets-encrypt-certificate-is-issued-and-renewed.md) <sub>P123</sub>
- [Anatomy of a URL](notes/p148-anatomy-of-a-url.md) <sub>P148</sub>
- [The TLS handshake, drawn](notes/p303-the-tls-handshake-drawn.md) <sub>P303</sub>
- [HTTP/1.1 vs HTTP/2 vs HTTP/3](notes/p476-http-1-1-vs-http-2-vs-http-3.md) <sub>P476</sub>

</details>

<details>
<summary><b>IT operations &amp; incidents</b> · 8 notes</summary>

- [9 checks before a server goes live](notes/p089-9-checks-before-a-server-goes-live.md) <sub>P89</sub>
- [5 troubleshooting habits to unlearn](notes/p091-5-troubleshooting-habits-to-unlearn.md) <sub>P91</sub>
- [9 checks before handing a laptop to a new employee](notes/p122-9-checks-before-handing-a-laptop-to-a-new-employee.md) <sub>P122</sub>
- [The first 30 minutes of an outage](notes/p138-the-first-30-minutes-of-an-outage.md) <sub>P138</sub>
- [The incident triage path](notes/p577-the-incident-triage-path.md) <sub>P577</sub>
- [9 steps of a host incident](notes/p580-9-steps-of-a-host-incident.md) <sub>P580</sub>
- [The automation pipeline](notes/p667-the-automation-pipeline.md) <sub>P667</sub>
- [Four automation failures](notes/p669-four-automation-failures.md) <sub>P669</sub>

</details>

<details>
<summary><b>Storage &amp; infrastructure</b> · 8 notes</summary>

- [5 disk mistakes that lose data](notes/p083-5-disk-mistakes-that-lose-data.md) <sub>P83</sub>
- [Add a new disk to a Linux server](notes/p086-add-a-new-disk-to-a-linux-server.md) <sub>P86</sub>
- [ext4 vs XFS vs Btrfs](notes/p096-ext4-vs-xfs-vs-btrfs.md) <sub>P96</sub>
- [VMware vs Hyper-V vs Proxmox](notes/p118-vmware-vs-hyper-v-vs-proxmox.md) <sub>P118</sub>
- [Block vs File vs Object storage](notes/p129-block-vs-file-vs-object-storage.md) <sub>P129</sub>
- [Anatomy of an /etc/fstab line](notes/p174-anatomy-of-an-etc-fstab-line.md) <sub>P174</sub>
- [9 LVM commands every RHCSA needs](notes/p175-9-lvm-commands-every-rhcsa-needs.md) <sub>P175</sub>
- [RAID 0, 1, 5 and 10, drawn](notes/p273-raid-0-1-5-and-10-drawn.md) <sub>P273</sub>

</details>

<details>
<summary><b>Windows &amp; Active Directory</b> · 7 notes</summary>

- [9 Windows commands for network problems](notes/p093-9-windows-commands-for-network-problems.md) <sub>P93</sub>
- [9 Active Directory hygiene checks](notes/p100-9-active-directory-hygiene-checks.md) <sub>P100</sub>
- [5 Windows admin mistakes to stop](notes/p102-5-windows-admin-mistakes-to-stop.md) <sub>P102</sub>
- [Fix: The trust relationship between this workstation and the domain failed](notes/p110-fix-the-trust-relationship-between-this-workstation-and-the-domain-fai.md) <sub>P110</sub>
- [Quiz: 3 Active Directory questions](notes/p114-quiz-3-active-directory-questions.md) <sub>P114</sub>
- [Active Directory vs Entra ID](notes/p128-active-directory-vs-entra-id.md) <sub>P128</sub>
- [9 Windows commands to diagnose and repair a PC](notes/p130-9-windows-commands-to-diagnose-and-repair-a-pc.md) <sub>P130</sub>

</details>

<details>
<summary><b>Backup &amp; recovery</b> · 5 notes</summary>

- [9 checks for a backup you can trust](notes/p085-9-checks-for-a-backup-you-can-trust.md) <sub>P85</sub>
- [Backup and cost control](notes/p617-backup-and-cost-control.md) <sub>P617</sub>
- [The backup verification cheat sheet](notes/p618-the-backup-verification-cheat-sheet.md) <sub>P618</sub>
- [5 backup mistakes](notes/p620-5-backup-mistakes.md) <sub>P620</sub>
- [Quiz: 3 data questions](notes/p621-quiz-3-data-questions-2.md) <sub>P621</sub>

</details>

<details>
<summary><b>Application &amp; API security</b> · 3 notes</summary>

- [The HTTP security header cheat sheet](notes/p553-the-http-security-header-cheat-sheet.md) <sub>P553</sub>
- [Four header defences and what each stops](notes/p554-four-header-defences-and-what-each-stops.md) <sub>P554</sub>
- [The layers of web request defence](notes/p560-the-layers-of-web-request-defence.md) <sub>P560</sub>

</details>

<details>
<summary><b>Observability &amp; SRE</b> · 1 notes</summary>

- [Uptime math: what each nine really allows](notes/p116-uptime-math-what-each-nine-really-allows.md) <sub>P116</sub>

</details>


## What is in a note

Each file in [`notes/`](notes) is Markdown with a short header:

```yaml
---
id: p72
title: "9 curl commands for debugging websites"
sections: [it]              # it, devsecops, or [it, devsecops]
topic: "Web servers, TLS & HTTP"
tags: [Linux, curl, SysAdmin]
source: "LinkedIn post P72 · Linux series"
---
```

Then the parts: **Quick reference** (commands, checklists, tables), **Explained** (the full post), **In one line** (the short version) and, for script posts, **Script**.

## Folders

```text
notes/     271 notes, one Markdown file each (p072-....md)
scripts/   84 scripts from the posts (64 Python + 20 Bash)
```

---

Made by **Hosam Hani** ([s0sta](https://github.com/s0sta)) · [s0sta.com](https://s0sta.com) · [LinkedIn](https://www.linkedin.com/in/hosam-hani-abdelati) · Contact: [s0sta.com/#contact](https://s0sta.com/#contact)
