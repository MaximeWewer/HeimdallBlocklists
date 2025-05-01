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
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/all_blocklists_merged.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/duggytuxy_agressive_ips_dst_fr_be_blocklist.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists/spamhaus_drop.txt
```

Here are the URLs for the split versions:

```text
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/duggytuxy_agressive_ips_dst_fr_be_blocklist-aa.txt
https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/blocklists_split/spamhaus_drop-aa.txt
```

## Contributions

Contributions are welcome  to improve the project or integrate new blocklist sources. Feel free to open issues or submit pull requests.
