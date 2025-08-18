"""Blocklist statistics generator with geolocation and AS analysis."""

import logging
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import ipaddress
import requests
import geoip2.database
import geoip2.errors

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants for directories and database paths
BLOCKLISTS_IP_FREQUENCY: int = 10
BLOCKLISTS_DIR: Path = Path("./blocklists")
STATISTICS_DIR: Path = Path("./statistics")
MAXMIND_DIR: Path = Path("./maxmind")
MAXMIND_COUNTRY_DB: str = "GeoLite2-Country.mmdb"
MAXMIND_ASN_DB: str = "GeoLite2-ASN.mmdb"
MAXMIND_URL: Dict[str, str] = {
    "Country": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb",
    "ASN": "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-ASN.mmdb",
}

# Ensure necessary directories exist
BLOCKLISTS_DIR.mkdir(parents=True, exist_ok=True)
STATISTICS_DIR.mkdir(parents=True, exist_ok=True)
MAXMIND_DIR.mkdir(parents=True, exist_ok=True)
logging.info("Necessary directories checked or created.")

def download_maxmind_databases() -> None:
    """Download MaxMind GeoIP databases if not already present in the directory."""
    for db_type, url in MAXMIND_URL.items():
        file_path: Path = MAXMIND_DIR / f"GeoLite2-{db_type}.mmdb"
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
        country_reader = geoip2.database.Reader(MAXMIND_DIR / MAXMIND_COUNTRY_DB, locales=['en'])
        as_reader = geoip2.database.Reader(MAXMIND_DIR / MAXMIND_ASN_DB, locales=['en'])
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

def save_blocklists_statistics(stats: List[Tuple[str, int]]) -> None:
    """Save the blocklists statistics (file name and IP count) to a Markdown file."""
    # Sort the stats by IP count in descending order
    sorted_stats = sorted(stats, key=lambda x: x[1], reverse=True)
    markdown_path: Path = STATISTICS_DIR / 'blocklists_statistics.md'
    content: str = "# Blocklists Statistics\n| Blocklist Name | IP Count |\n|----|----|\n"
    content += "".join(f"| {name} | {count} |\n" for name, count in sorted_stats)
    markdown_path.write_text(content)
    logging.info(f"Statistics saved to {markdown_path}")

def get_unique_ips() -> Set[str]:
    """Aggregate and return unique IPs from all blocklist files in the directory,
    along with the stats for each file."""
    unique_ips: Set[str] = set()
    blocklist_stats: List[Tuple[str, int]] = []

    for file_path in BLOCKLISTS_DIR.glob("*.txt"):
        ips = extract_ips_from_file(file_path)
        unique_ips.update(ips)
        blocklist_stats.append((file_path.name, len(ips)))

    save_blocklists_statistics(blocklist_stats)
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
    title: str = entries[0]
    header: str = entries[1]
    separator: str = entries[2]
    data_entries: List[str] = entries[3:]

    # Parse data entries into a list of tuples (date, line)
    parsed_entries = []
    for line in data_entries:
        parts = line.split('|')
        if len(parts) == 4:  # Ensure it's a valid row
            date_str = parts[1].strip()
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                parsed_entries.append((date_obj, line))
            except ValueError:
                logging.warning(f"Skipping invalid row: {line}")

    # Update or append today's entry
    updated = False
    for i, (date_obj, line) in enumerate(parsed_entries):
        if today in line:
            parsed_entries[i] = (date_obj, f"| {today} | {unique_ip_count} |")
            updated = True
            break
    if not updated:
        parsed_entries.append((datetime.strptime(today, "%Y-%m-%d"), f"| {today} | {unique_ip_count} |"))

    # Sort entries by date in descending order and keep the last 30 days
    parsed_entries = sorted(parsed_entries, key=lambda x: x[0], reverse=True)[:30]

    # Rebuild the data entries
    data_entries = [line for _, line in parsed_entries]

    # Combine header, separator, and data entries into a single Markdown string
    markdown_content = "\n".join([title.strip(), header.strip(), separator.strip()] + data_entries)
    markdown_path.write_text(markdown_content, encoding='utf-8')
    logging.info(f"Daily summary updated with {unique_ip_count} unique IPs for {today}.")

def read_existing_summary(file_path: Path) -> List[str]:
    """Read existing daily summary and return as a list of lines, or initialize if file does not exist."""
    if file_path.exists():
        content = file_path.read_text(encoding='utf-8').strip()
        if content:  # Ensure the file is not empty
            return content.splitlines()
    # Return a properly formatted header if the file does not exist or is empty
    return [
        "# Daily IP Summary",
        "| Date | Unique IP Count |",
        "|----|----|"
    ]

def analyze_ip_blocklists_frequency(unique_ips: Set[str], blocklists: List[Set[str]]) -> Dict[int, int]:
    """Analyze how many IPs are present in at least a specified number of blocklists."""
    frequency_counter = defaultdict(int)

    for ip in unique_ips:
        count = sum(1 for blocklist in blocklists if ip in blocklist)
        if count <= BLOCKLISTS_IP_FREQUENCY:
            frequency_counter[count] += 1

    return frequency_counter

def save_blocklist_frequency_statistics(frequency_counter: Dict[int, int]) -> None:
    """Save the blocklist frequency statistics to a Markdown file."""
    total_ips = sum(frequency_counter.values())
    data = [(f"Present in {count} blocklist{'s' if count > 1 else ''}", num_ips, f"{(num_ips / total_ips) * 100:.2f}%") for count, num_ips in sorted(frequency_counter.items())]
    markdown_path = STATISTICS_DIR / 'blocklists_ip_frequency_statistics.md'
    headers = ["Malicious IP", "Number of IPs", "%"]
    save_statistics_file(data, markdown_path, headers, "IP presence frequency in blocklists")

def save_statistics_file(data: List[Tuple[str, int, str]], file_path: Path, headers: List[str], title: str) -> None:
    """Save statistics to a Markdown file with a given title and headers."""
    content: str = f"# {title}\n| " + " | ".join(headers) + " |\n" + \
                   "|" + "|".join(['-' * 4 for _ in headers]) + "|\n"
    content += "".join([f"| {row[0]} | {row[1]} | {row[2]} |\n" for row in data])
    file_path.write_text(content)
    logging.info(f"Statistics saved to {file_path}")

def save_statistics(unique_ips: Set[str], country_stats: Counter, as_stats: Counter, frequency_counter: Dict[int, int]) -> None:
    """Save all statistics including daily summary, country, AS distribution, and blocklist frequency."""
    # Save daily IP summary
    save_daily_summary(len(unique_ips))

    # Save country distribution statistics
    country_data = [(country, count, f"{(count / sum(country_stats.values())) * 100:.2f}%") for country, count in country_stats.most_common(100)]
    save_statistics_file(country_data, STATISTICS_DIR / 'country_distribution.md', ["Country", "Count", "Percentage"], "Top 100 Country Distribution")

    # Save AS distribution statistics
    as_data = [(as_name, count, f"{(count / sum(as_stats.values())) * 100:.2f}%") for as_name, count in as_stats.most_common(100)]
    save_statistics_file(as_data, STATISTICS_DIR / 'as_distribution.md', ["AS", "Count", "Percentage"], "Top 100 AS Distribution")

    # Save blocklist frequency statistics
    save_blocklist_frequency_statistics(frequency_counter)

def main() -> None:
    """Main function to orchestrate the statistics generation process."""
    logging.info("Starting blocklist statistics generation")
    
    try:
        # Download databases if needed
        download_maxmind_databases()
        
        # Load GeoIP databases
        country_reader, as_reader = load_geoip_databases()

        if country_reader is None or as_reader is None:
            logging.error("GeoIP databases are not loaded. Exiting.")
            return
            
        try:
            # Get unique IPs from all blocklists
            unique_ips = get_unique_ips()
            
            if not unique_ips:
                logging.warning("No unique IPs found in blocklists")
                return

            # Load all blocklist IPs for frequency analysis
            logging.info("Loading blocklist files for frequency analysis")
            blocklists = [
                extract_ips_from_file(file_path) 
                for file_path in BLOCKLISTS_DIR.glob("*.txt")
            ]

            # Perform country and AS analysis
            logging.info("Starting geolocation and AS analysis")
            country_stats, as_stats = analyze_ips(
                unique_ips, 
                country_reader, 
                as_reader
            )

            # Analyze blocklist frequency
            logging.info("Starting frequency analysis")
            frequency_counter = analyze_ip_blocklists_frequency(
                unique_ips, 
                blocklists
            )

            # Save all statistics
            logging.info("Saving statistics")
            save_statistics(
                unique_ips, 
                country_stats, 
                as_stats, 
                frequency_counter
            )
            
            logging.info("Statistics generation completed successfully")
            
        finally:
            # Ensure databases are closed
            if country_reader:
                country_reader.close()
            if as_reader:
                as_reader.close()
                
    except Exception as e:
        logging.error(f"Statistics generation failed: {e}")
        raise


if __name__ == "__main__":
    main()
