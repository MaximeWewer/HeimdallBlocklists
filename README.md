# HeimdallBlocklists

HeimdallBlocklists is a project designed to merge and manage multiple community-maintained blocklists, making them easily usable across various firewall solutions.

## Features

- **Blocklist Merging**: Combines different community blocklists into unified and easily manageable lists.
- **Compatibility**: Blocklists are split into segments of 130,000 lines to works seamlessly with all major firewalls, ensuring wide applicability.
- **Easy Configuration**: Simply modify the JSON configuration file to add new blocklist sources effortlessly.


## Example Blocklists

HeimdallBlocklists uses well-known sources, such as:

- AbuseIP
- AlienVault
- Cinsscore
- ISC SANS Edu
- Spamhaus
- etc.

We extend credit to the contributors who maintain these vital blocklists for the community, such as :

- DuggyTuxy : <https://github.com/duggytuxy/malicious_ip_addresses>
- Romain Marcoux : <https://github.com/romainmarcoux/malicious-ip>

## Blocklists URLs

Here are the URLs for the community blocklists and their split versions:

```text
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/3coresec_lists_all.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/duggytuxy_botnets_zombies_scanner_spam_ips.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_abuseipdb-s100-120d.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/romainmarcoux_akamai.com.txt
```

```text
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/3coresec_lists_all-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/duggytuxy_botnets_zombies_scanner_spam_ips-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/duggytuxy_botnets_zombies_scanner_spam_ips-ab.txt
```


## Contributions

We welcome contributions to improve the project or integrate new blocklist sources. Feel free to open issues or submit pull requests.
