import re
import time
import logging
import requests
import ipaddress
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants and configuration
OUTPUT_DIR: Path = Path("Travaux/Whitelists_blocklists/blocklists")

# Base URLs for the lists to download
ROMAINMARCOUX_GITHUB_URL: str = "https://github.com/romainmarcoux/malicious-ip/tree/main/sources"
ROMAINMARCOUX_RAW_URL_PREFIX: str = "https://raw.githubusercontent.com/romainmarcoux/malicious-ip/main/sources"
DUGGYTUXY_URL: str = "https://raw.githubusercontent.com/duggytuxy/malicious_ip_addresses/refs/heads/main/botnets_zombies_scanner_spam_ips.txt"
THREE_CORESEC_URL: str = "https://blacklist.3coresec.net/lists/all.txt"
SPAMHAUS_DROP_URL: str = "https://www.spamhaus.org/drop/drop.txt"

MAX_RETRIES: int = 10
RETRY_DELAY: int = 2  # Seconds between each attempt

# Ensure necessary directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
logging.info("Necessary directories checked or created.")

def clear_directory(directory: Path) -> None:
    """Remove all contents of the specified directory."""
    for file_path in directory.iterdir():
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                file_path.rmdir()
        except Exception as e:
            logging.error(f"Error removing {file_path}: {e}")

def get_file_list_from_github() -> List[str]:
    """Retrieve the list of blocklist files from GitHub with retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(ROMAINMARCOUX_GITHUB_URL, timeout=5)
            if response.status_code == 200:
                file_list = re.findall(r'href="[^"]*\.txt"', response.text)
                if file_list:
                    return [
                        f"{ROMAINMARCOUX_RAW_URL_PREFIX}/{file.split('/')[-1].replace('\"', '')}"
                        for file in file_list
                    ]
        except requests.RequestException as e:
            logging.error(f"Attempt {attempt}: Connection error - {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)
    logging.error("Failed to retrieve the file list after several attempts.")
    return []

def download_file(url: str, filename: str) -> None:
    """Download a file from a given URL into OUTPUT_DIR."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            file_path = OUTPUT_DIR / filename
            file_path.write_bytes(response.content)
            logging.info(f"Downloaded {filename}")
        else:
            logging.error(f"Error downloading {filename}: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Error connecting to {url}: {e}")

def download_all_files(file_urls: List[str]) -> None:
    """Download all files using multithreading."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        for url in file_urls:
            filename = url.split("/")[-1]
            executor.submit(download_file, url, filename)

def romainmarcoux_merge_files(file_prefix: str) -> Path:
    """Merge fragments of files with the same prefix into a single file."""
    merged_file_path = OUTPUT_DIR / f"romainmarcoux_{file_prefix}.txt"
    with merged_file_path.open('w', encoding='utf-8', errors='ignore') as merged_file:
        for filename in sorted(OUTPUT_DIR.glob(f"{file_prefix}-a*.txt")):
            with filename.open('r', encoding='utf-8', errors='ignore') as fragment:
                merged_file.write(fragment.read())
    return merged_file_path

def is_valid_ip(ip: str) -> bool:
    """Return True if the given IP address is valid, otherwise False."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def extract_and_sort_ipv4(file_path: Path) -> None:
    """Extract all IPv4 addresses from a file, validate, sort, and overwrite the file."""
    with file_path.open('r', encoding='utf-8', errors='ignore') as f:
        ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', f.read())
    sorted_ips = sorted({ip for ip in ips if is_valid_ip(ip)}, key=ipaddress.ip_address)
    with file_path.open('w', encoding='utf-8', errors='ignore') as f:
        f.write("\n".join(sorted_ips))

def clean_and_merge_fragments(prefixes: List[str]) -> None:
    """Merge, extract, and sort IPs in files with specified prefixes, then delete fragments."""
    for prefix in prefixes:
        merged_file_path = romainmarcoux_merge_files(prefix)
        extract_and_sort_ipv4(merged_file_path)
        for fragment in OUTPUT_DIR.glob(f"{prefix}-a*.txt"):
            fragment.unlink()

def handle_list(url: str, filename: str, source_name: str) -> None:
    """Download and process a list from a given URL."""
    download_file(url, filename)
    
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or file_path.stat().st_size == 0:
        logging.error(f"No files found for {source_name} or the file is empty.")
    else:
        extract_and_sort_ipv4(file_path)

def handle_duggytuxy_list() -> None:
    """Download and process the DuggyTuxy list."""
    handle_list(DUGGYTUXY_URL, "duggytuxy_botnets_zombies_scanner_spam_ips.txt", "DuggyTuxy")

def handle_3coresec_list() -> None:
    """Download and process the 3coresec list."""
    handle_list(THREE_CORESEC_URL, "3coresec_lists_all.txt", "3coresec")

def handle_spamhaus_list() -> None:
    """Download and process the Spamhaus list."""
    handle_list(SPAMHAUS_DROP_URL, "spamhaus_drop.txt", "Spamhaus")

def handle_romainmarcoux_lists() -> None:
    """Download and merge Romain Marcoux's list fragments, then extract IPv4 addresses."""
    file_list = get_file_list_from_github()
    if not file_list:
        logging.error("No files found for Romain Marcoux.")
        return

    download_all_files(file_list)

    # Remove empty files
    for filename in OUTPUT_DIR.iterdir():
        if filename.is_file() and filename.stat().st_size == 0:
            filename.unlink()

    # Identify prefixes and merge fragments
    prefixes = {re.sub(r"-(a[a-z])\.txt$", "", f.name) for f in OUTPUT_DIR.glob("*-a*.txt")}
    clean_and_merge_fragments(list(prefixes))

if __name__ == "__main__":
    clear_directory(OUTPUT_DIR)
    handle_duggytuxy_list()
    handle_romainmarcoux_lists()
    handle_3coresec_list()
    handle_spamhaus_list()
