# HeimdallBlocklists

HeimdallBlocklists is a project designed to merge and manage multiple community-maintained blocklists, making them easily usable across various firewall solutions.

## Features

- **Blocklist Merging**: Combines different community blocklists into unified and easily manageable lists.
- **Compatibility**: Blocklists are split into segments of 130,000 lines to works seamlessly with all major firewalls, ensuring wide applicability.
- **Easy Configuration**: Simply modify the JSON configuration file to add new blocklist sources effortlessly.
- **IP Statistics**: Provides statistics on the number of blocked IPs, autonomous systems (AS), countries, etc.

## Example Blocklists

HeimdallBlocklists uses well-known sources, such as:

- AbuseIP
- AlienVault
- Cinsscore
- ISC SANS Edu
- Spamhaus
- etc.

The contributors who maintain these blocklists deserve your support, thanks to:

- DuggyTuxy : <https://github.com/duggytuxy/malicious_ip_addresses>
- Romain Marcoux : <https://github.com/romainmarcoux/malicious-ip>

## Blocklists URLs

Here are the URLs for the community blocklists:

```text
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/duggytuxy_botnets_zombies_scanner_spam_ips.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_abuseipdb-s100-120d.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_alienvault-fakelabs.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_alienvault-georgs.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_alienvault-ssh-bruteforce.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_binarydefense.com.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_blocklist.de-all.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_cinsscore.com.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_emergingthreats.net.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_greensnow.co.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_isc.sans.edu.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_malicious-ip.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_projecthoneypot.org.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_sekio.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_snort.org.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_stamparm.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/spamhaus_drop.txt
```

Here are the URLs for the split versions:

```text
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/duggytuxy_botnets_zombies_scanner_spam_ips-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_abuseipdb-s100-120d-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_abuseipdb-s100-120d-ab.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_abuseipdb-s100-120d-ac.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_abuseipdb-s100-120d-ad.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_alienvault-fakelabs-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_alienvault-georgs-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_alienvault-ssh-bruteforce-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_binarydefense.com-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_blocklist.de-all-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_cinsscore.com-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_emergingthreats.net-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_greensnow.co-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_isc.sans.edu-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_isc.sans.edu-ab.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_malicious-ip-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_malicious-ip-ab.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_projecthoneypot.org-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_sekio-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_snort.org-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_stamparm-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/romainmarcoux_stamparm-ab.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/spamhaus_drop-aa.txt
```

## Contributions

Contributions are welcome  to improve the project or integrate new blocklist sources. Feel free to open issues or submit pull requests.
