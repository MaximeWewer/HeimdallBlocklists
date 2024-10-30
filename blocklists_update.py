import re
import json
import string
import time
import logging
import requests
import ipaddress
from typing import Dict, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants and configuration
CONFIG_FILE: Path = Path('./blocklists_config.json')
BLOCKLISTS_DIR: Path = Path("./blocklists")
BLOCKLISTS_SPLIT_DIR: Path = Path("./blocklists_split")
MAX_LINES_PER_FILE = 130000
MAX_RETRIES: int = 10
RETRY_DELAY: int = 2  # Seconds between each attempt

# Ensure necessary directory exists
BLOCKLISTS_DIR.mkdir(parents=True, exist_ok=True)
BLOCKLISTS_SPLIT_DIR.mkdir(parents=True, exist_ok=True)
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

def remove_empty_files(directory: Path) -> None:
    """Remove all empty files from the specified directory."""
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.stat().st_size == 0:
            file_path.unlink()

def get_fragment_list(github_url: str, raw_url_prefix: str) -> List[str]:
    """Retrieve the list of fragment files from GitHub with retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(github_url, timeout=5)
            if response.status_code == 200:
                fragment_list = set(re.findall(r'href="([^"]*\.txt)"', response.text))
                if fragment_list:
                    return [
                        f"{raw_url_prefix}/{file.split('/')[-1].replace('\"', '')}"
                        for file in fragment_list
                    ]
        except requests.RequestException as e:
            logging.error(f"Attempt {attempt}: Connection error - {e}")
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)
    logging.error("Failed to retrieve the file list after several attempts.")
    return []

def download_file(url: str, filename: str) -> None:
    """Download a file from a given URL into BLOCKLISTS_DIR."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            file_path = BLOCKLISTS_DIR / filename
            file_path.write_bytes(response.content)
            logging.info(f"Downloaded {filename}")
        else:
            logging.error(f"Error downloading {filename}: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Error connecting to {url}: {e}")

def download_all_files(file_urls: List[str]) -> None:
    """Download all files using multithreading."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        for url in sorted(file_urls):
            filename = url.split("/")[-1]
            executor.submit(download_file, url, filename)

def merge_fragments(prefix: str, blocklist_name: str) -> Path:
    """Merge fragments of files with the same prefix into a single file."""
    merged_file_path = BLOCKLISTS_DIR / f"{prefix}_{blocklist_name}.txt"
    with merged_file_path.open('w', encoding='utf-8', errors='ignore') as merged_file:
        for filename in sorted(BLOCKLISTS_DIR.glob(f"{blocklist_name}-a*.txt")):
            with filename.open('r', encoding='utf-8', errors='ignore') as fragment:
                merged_file.write(fragment.read())
    return merged_file_path

def merge_and_clean_fragments(merge_prefix: str) -> None:
    """Extract, merge, and sort IPs in files with specified prefixes, then delete fragments."""
    blocklists_names = sorted({re.sub(r"-(a[a-z])\.txt$", "", f.name) for f in BLOCKLISTS_DIR.glob("*-a*.txt")})
    for name in blocklists_names:
        merged_file_path = merge_fragments(merge_prefix, name)
        extract_and_sort_ipv4(merged_file_path)
        for fragment in BLOCKLISTS_DIR.glob(f"{name}-a*.txt"):
            fragment.unlink()

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

def load_config(file_path: Path) -> List[Dict[str, str]]:
    """Load configuration from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def handle_resource(resource: Dict[str, str]) -> None:
    """Download and process a resource based on the configuration."""
    if "github_url" in resource and "raw_url_prefix" in resource:
        file_urls = get_fragment_list(resource["github_url"], resource["raw_url_prefix"])
        if file_urls:
            download_all_files(file_urls)
            remove_empty_files(BLOCKLISTS_DIR)
            merge_and_clean_fragments(resource["merge_prefix"])
    elif "url" in resource and "filename" in resource:
        download_file(resource["url"], resource["filename"])
        remove_empty_files(BLOCKLISTS_DIR)
        file_path = BLOCKLISTS_DIR / resource["filename"]
        if file_path:
            extract_and_sort_ipv4(file_path)

def process_all_resources(config_file: Path) -> None:
    """Load resources configuration and process each resource."""
    resources = load_config(config_file)
    for resource in resources:
        handle_resource(resource)

def split_large_blocklists(input_directory: Path, output_directory: Path, max_lines: int) -> None:
    """
    Splits large blocklist files from the input directory if they exceed a given number of lines.
    Renames files according to the pattern `name-aa.txt`, `name-ab.txt`, etc., and writes them to the output directory.
    """
    for file_path in input_directory.iterdir():
        if file_path.is_file() and file_path.suffix == '.txt':
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            line_count = len(lines)
            base_name = file_path.stem

            if line_count <= max_lines:
                # Rename the file to include the pattern `name-aa.txt`
                new_file_name = f"{base_name}-aa.txt"
                output_file_path = output_directory / new_file_name
                with output_file_path.open('w', encoding='utf-8') as output_file:
                    output_file.writelines(lines)
            else:
                # Generate the file name pattern
                alphabet = string.ascii_lowercase
                part_index = 0
                start_line = 0

                # Split and save parts with incrementing suffixes
                while start_line < line_count:
                    end_line = min(start_line + max_lines, line_count)
                    part_suffix = f"{alphabet[part_index // 26]}{alphabet[part_index % 26]}"
                    part_file_name = f"{base_name}-{part_suffix}.txt"
                    part_file_path = output_directory / part_file_name
                    
                    # Write the split file
                    with part_file_path.open('w', encoding='utf-8') as part_file:
                        part_file.writelines(lines[start_line:end_line])
                    
                    start_line += max_lines
                    part_index += 1

if __name__ == "__main__":
    clear_directory(BLOCKLISTS_DIR)
    process_all_resources(CONFIG_FILE)
    split_large_blocklists(BLOCKLISTS_DIR, BLOCKLISTS_SPLIT_DIR, MAX_LINES_PER_FILE)
