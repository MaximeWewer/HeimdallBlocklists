import re
import logging
import requests
import ipaddress
import geoip2.database, geoip2.errors
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Tuple, Optional, List, Dict, Set

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants for directories and database paths
OUTPUT_DIR: Path = Path("Travaux/Whitelists_blocklists/blocklists")
STATISTICS_DIR: Path = Path("Travaux/Whitelists_blocklists/statistics")
MAXMIND_PATH: Path = Path("maxmind")
MAXMIND_COUNTRY_DB: str = "GeoLite2-Country.mmdb"
MAXMIND_ASN_DB: str = "GeoLite2-ASN.mmdb"
MAXMIND_URL: Dict[str, str] = {
    "Country": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb",
    "ASN": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb",
}

# Ensure necessary directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATISTICS_DIR.mkdir(parents=True, exist_ok=True)
MAXMIND_PATH.mkdir(parents=True, exist_ok=True)
logging.info("Necessary directories checked or created.")

def download_maxmind_databases() -> None:
    """Download MaxMind GeoIP databases if not already present in the directory."""
    for db_type, url in MAXMIND_URL.items():
        file_path: Path = MAXMIND_PATH / f"GeoLite2-{db_type}.mmdb"
        if not file_path.exists():
            logging.info(f"Downloading {db_type} database...")
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                file_path.write_bytes(response.content)
                logging.info(f"{db_type} database downloaded successfully.")
            except requests.RequestException as e:
                logging.error(f"Failed to download {db_type} database: {e}")

def load_geoip_databases() -> Tuple[Optional[geoip2.database.Reader], Optional[geoip2.database.Reader]]:
    """Load the GeoIP databases for country and AS lookups."""
    try:
        country_reader = geoip2.database.Reader(MAXMIND_PATH / MAXMIND_COUNTRY_DB, locales=['en'])
        as_reader = geoip2.database.Reader(MAXMIND_PATH / MAXMIND_ASN_DB, locales=['en'])
        logging.info("GeoIP databases loaded successfully.")
        return country_reader, as_reader
    except Exception as e:
        logging.error(f"Error loading GeoIP databases: {e}")
        return None, None

def is_valid_ip(ip: str) -> bool:
    """Return True if the given IP address is valid, otherwise False."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        logging.warning(f"Invalid IP address found: {ip}")
        return False

def extract_ips_from_file(file_path: Path) -> Set[str]:
    """Extract and return a set of valid IPs from a given file."""
    try:
        content: str = file_path.read_text(encoding='utf-8', errors='ignore')
        ips: List[str] = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', content)
        valid_ips: Set[str] = {ip for ip in ips if is_valid_ip(ip)}
        return valid_ips
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return set()

def save_blocklist_statistics(stats: List[Tuple[str, int]]) -> None:
    """Save the blocklist statistics (file name and IP count) to a Markdown file."""
    markdown_path: Path = STATISTICS_DIR / 'blocklist_statistics.md'
    content: str = "# Blocklist Statistics\n| Blocklist Name | IP Count |\n|----|----|\n"
    content += "".join(f"| {name} | {count} |\n" for name, count in stats)
    markdown_path.write_text(content)
    logging.info(f"Statistics saved to {markdown_path}")

def get_unique_ips() -> Set[str]:
    """Aggregate and return unique IPs from all blocklist files in the directory,
    along with the stats for each file."""
    unique_ips: Set[str] = set()
    blocklist_stats: List[Tuple[str, int]] = []

    for file_path in OUTPUT_DIR.glob("*.txt"):
        ips = extract_ips_from_file(file_path)
        unique_ips.update(ips)
        blocklist_stats.append((file_path.name, len(ips)))

    save_blocklist_statistics(blocklist_stats)
    return unique_ips

def analyze_ips(unique_ips: Set[str], country_reader: geoip2.database.Reader, as_reader: geoip2.database.Reader) -> Tuple[Counter, Counter]:
    """Analyze IP addresses for country and AS distribution using Counter."""
    country_stats: Counter = Counter()
    as_stats: Counter = Counter()

    for ip in unique_ips:
        country: Optional[str] = lookup_country(ip, country_reader)
        if country:
            country_stats[country] += 1

        as_name: Optional[str] = lookup_as(ip, as_reader)
        if as_name:
            as_stats[as_name] += 1

    logging.info("IP analysis completed.")
    return country_stats, as_stats

def lookup_country(ip: str, reader: geoip2.database.Reader) -> Optional[str]:
    """Return the country name for a given IP using the GeoIP reader, or None if not found."""
    try:
        return reader.country(ip).country.name
    except geoip2.errors.AddressNotFoundError:
        return None

def lookup_as(ip: str, reader: geoip2.database.Reader) -> Optional[str]:
    """Return the AS name for a given IP using the GeoIP reader, or None if not found."""
    try:
        return reader.asn(ip).autonomous_system_organization
    except geoip2.errors.AddressNotFoundError:
        return None

def save_daily_summary(unique_ip_count: int) -> None:
    """Save the daily unique IP count in a Markdown file, retaining data for the last 30 days."""
    today: str = datetime.now().strftime("%Y-%m-%d")
    markdown_path: Path = STATISTICS_DIR / 'daily_ip_summary.md'
    entries: List[str] = read_existing_summary(markdown_path)

    # Separate header and data entries
    header: str = entries[0]
    separator: str = entries[1]
    data_entries: List[str] = entries[2:]

    # Update or append today's entry
    updated: bool = False
    for i, line in enumerate(data_entries):
        if today in line:
            data_entries[i] = f"| {today} | {unique_ip_count} |"
            updated = True
            break
    if not updated:
        data_entries.append(f"| {today} | {unique_ip_count} |")

    # Keep only the last 30 days of entries
    data_entries = data_entries[-30:]

    # Combine header, separator, and data entries into a single Markdown string without extra line breaks
    markdown_content: str = "".join([header, separator] + data_entries)
    markdown_path.write_text(markdown_content)
    logging.info(f"Daily summary updated with {unique_ip_count} unique IPs for {today}.")

def read_existing_summary(file_path: Path) -> List[str]:
    """Read existing daily summary and return as a list of lines, or initialize if file does not exist."""
    if file_path.exists():
        return file_path.read_text().strip().splitlines()
    return ["# Daily IP Summary\n", "| Date | Unique IP Count |\n", "|----|----|\n"]

def save_statistics_file(data: List[Tuple[str, int, str]], file_path: Path, headers: List[str], title: str) -> None:
    """Save statistics to a Markdown file with a given title and headers."""
    content: str = f"# {title}\n| " + " | ".join(headers) + " |\n" + \
                   "|" + "|".join(['-' * 4 for _ in headers]) + "|\n"
    content += "".join([f"| {row[0]} | {row[1]} | {row[2]} |\n" for row in data])
    file_path.write_text(content)
    logging.info(f"Statistics saved to {file_path}")

def save_statistics(unique_ips: Set[str], country_stats: Counter, as_stats: Counter) -> None:
    """Save country and AS distribution statistics to Markdown files."""
    save_daily_summary(len(unique_ips))

    country_data: List[Tuple[str, int, str]] = [(country, count, f"{(count / sum(country_stats.values())) * 100:.2f}%") for country, count in country_stats.most_common(100)]
    save_statistics_file(country_data, STATISTICS_DIR / 'country_distribution.md', ["Country", "Count", "Percentage"], "Top 100 Country Distribution")

    as_data: List[Tuple[str, int, str]] = [(as_name, count, f"{(count / sum(as_stats.values())) * 100:.2f}%") for as_name, count in as_stats.most_common(100)]
    save_statistics_file(as_data, STATISTICS_DIR / 'asn_distribution.md', ["ASN", "Count", "Percentage"], "Top 100 ASN Distribution")

def main() -> None:
    """Main function to orchestrate the workflow."""
    download_maxmind_databases()
    country_reader, as_reader = load_geoip_databases()

    if country_reader is None or as_reader is None:
        logging.error("GeoIP databases are not loaded. Exiting.")
        return

    unique_ips = get_unique_ips()
    country_stats, as_stats = analyze_ips(unique_ips, country_reader, as_reader)
    save_statistics(unique_ips, country_stats, as_stats)

    # Clean up readers
    country_reader.close()
    as_reader.close()

if __name__ == "__main__":
    main()
