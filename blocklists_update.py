"""Blocklist update module for downloading and processing IP blocklists."""

import json
import logging
import os
import re
import string
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

import ipaddress
import requests

# Setup logger
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants and configuration
CONFIG_FILE: Path = Path("./blocklists_config.json")
BLOCKLISTS_DIR: Path = Path("./blocklists")
BLOCKLISTS_SPLIT_DIR: Path = Path("./blocklists_split")
BLOCKLISTS_MERGED_FILE_PATH: Path = (
    Path("./blocklists/all_blocklists_merged.txt")
)
MAX_LINES_PER_FILE: int = 130000
MAX_RETRIES: int = 10
RETRY_DELAY: int = 2  # Seconds between each attempt
REQUEST_TIMEOUT: int = 5

# Ensure necessary directory exists
BLOCKLISTS_DIR.mkdir(parents=True, exist_ok=True)
BLOCKLISTS_SPLIT_DIR.mkdir(parents=True, exist_ok=True)
logging.info("Necessary directories checked or created")

def clear_directory(directory: Path) -> None:
    """Remove all contents of the specified directory.
    
    Args:
        directory: Path object pointing to the directory to clear.
    """
    for file_path in directory.iterdir():
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                file_path.rmdir()
        except OSError as e:
            logging.error(f"Error removing {file_path}: {e}")

def remove_empty_files(directory: Path) -> None:
    """Remove all empty files from the specified directory.
    
    Args:
        directory: Path object pointing to the directory to clean.
    """
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.stat().st_size == 0:
            try:
                file_path.unlink()
                logging.debug(f"Removed empty file: {file_path}")
            except OSError as e:
                logging.error(f"Error removing empty file {file_path}: {e}")

def get_fragment_list(github_url: str) -> List[str]:
    """Retrieve the list of fragment files from GitHub with retries.
    
    Args:
        github_url: GitHub repository URL to scrape for files.
        raw_url_prefix: Base URL prefix for raw GitHub content.
        
    Returns:
        List of URLs to text files found in the repository.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(github_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            if response.status_code == 200:
                # Extract JSON data from GitHub's React app
                json_match = re.search(
                    r'<script type="application/json" data-target="react-app.embeddedData">(.*?)</script>',
                    response.text,
                    re.DOTALL
                )
                
                if not json_match:
                    logging.error("Could not find embedded JSON data")
                    continue
                    
                data = json.loads(json_match.group(1))
                
                files = data["payload"]["tree"]["items"]
                repo = data["payload"]["repo"]
                branch = data["payload"]["refInfo"]["name"]
                owner = repo["ownerLogin"]
                repo_name = repo["name"]
                
                txt_files = [
                    item["path"] for item in files 
                    if item["path"].endswith(".txt")
                ]
                
                return [
                    f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{file_path}"
                    for file_path in txt_files
                ]
                
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            logging.error(f"Attempt {attempt}: Error retrieving fragment list - {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    
    logging.error("Failed to retrieve the file list after several attempts")
    return []

def download_file(url: str, filename: str) -> None:
    """Download a file from a given URL into BLOCKLISTS_DIR.
    
    Args:
        url: URL to download the file from.
        filename: Name to save the file as.
    """
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        file_path = BLOCKLISTS_DIR / filename
        file_path.write_bytes(response.content)
        logging.info(f"Downloaded {filename}")
        
    except requests.RequestException as e:
        logging.error(f"Error downloading {filename} from {url}: {e}")

def download_all_files(file_urls: List[str]) -> None:
    """Download all files using multithreading.
    
    Args:
        file_urls: List of URLs to download.
    """
    max_workers = min(os.cpu_count() or 4, len(file_urls))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for url in sorted(file_urls):
            filename = url.split("/")[-1]
            executor.submit(download_file, url, filename)

def merge_fragments(prefix: str, blocklist_name: str) -> Path:
    """Merge fragments of files with the same prefix into a single file.
    
    Args:
        prefix: Prefix to use for the merged file name.
        blocklist_name: Base name of the blocklist.
        
    Returns:
        Path to the merged file.
    """
    merged_file_path = BLOCKLISTS_DIR / f"{prefix}_{blocklist_name}.txt"
    
    with merged_file_path.open("w", encoding="utf-8", errors="ignore") as merged_file:
        for filename in sorted(BLOCKLISTS_DIR.glob(f"{blocklist_name}-a*.txt")):
            with filename.open("r", encoding="utf-8", errors="ignore") as fragment:
                merged_file.write(fragment.read())
                
    return merged_file_path

def merge_and_clean_fragments(merge_prefix: str) -> None:
    """Extract, merge, and sort IPs in files with specified prefixes, then delete fragments.
    
    Args:
        merge_prefix: Prefix to use for merged files.
    """
    blocklists_names = sorted({
        re.sub(r"-(a[a-z])\.txt$", "", f.name) 
        for f in BLOCKLISTS_DIR.glob("*-a*.txt")
    })
    
    for name in blocklists_names:
        merged_file_path = merge_fragments(merge_prefix, name)
        extract_and_sort_ipv4(merged_file_path)
        
        # Clean up fragment files
        for fragment in BLOCKLISTS_DIR.glob(f"{name}-a*.txt"):
            try:
                fragment.unlink()
            except OSError as e:
                logging.error(f"Error removing fragment {fragment}: {e}")

def is_valid_ip(ip: str) -> bool:
    """Return True if the given IP address is valid, otherwise False.
    
    Args:
        ip: IP address string to validate.
        
    Returns:
        True if IP is valid, False otherwise.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def extract_and_sort_ipv4(file_path: Path) -> None:
    """Extract all IPv4 addresses from a file, validate, sort, and overwrite the file.
    
    Args:
        file_path: Path to the file to process.
    """
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        ips = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", content)
        valid_unique_ips = {ip for ip in ips if is_valid_ip(ip)}
        sorted_ips = sorted(valid_unique_ips, key=ipaddress.ip_address)
        
        with file_path.open("w", encoding="utf-8", errors="ignore") as f:
            f.write("\n".join(sorted_ips))
            
        logging.debug(f"Processed {len(sorted_ips)} unique IPs in {file_path}")
        
    except OSError as e:
        logging.error(f"Error processing file {file_path}: {e}")

def load_config(file_path: Path) -> List[Dict[str, str]]:
    """Load configuration from a JSON file.
    
    Args:
        file_path: Path to the JSON configuration file.
        
    Returns:
        List of configuration dictionaries.
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist.
        json.JSONDecodeError: If the JSON is invalid.
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file {file_path}: {e}")
        raise

def handle_resource(resource: Dict[str, str]) -> None:
    """Download and process a resource based on the configuration.
    
    Args:
        resource: Dictionary containing resource configuration.
    """
    if "github_url" in resource:
        file_urls = get_fragment_list(
            resource["github_url"]
        )
        if file_urls:
            download_all_files(file_urls)
            remove_empty_files(BLOCKLISTS_DIR)
            merge_and_clean_fragments(resource["merge_prefix"])
        else:
            logging.warning(f"No files found for resource: {resource}")
            
    elif "url" in resource and "filename" in resource:
        download_file(resource["url"], resource["filename"])
        remove_empty_files(BLOCKLISTS_DIR)
        
        file_path = BLOCKLISTS_DIR / resource["filename"]
        if file_path.exists():
            extract_and_sort_ipv4(file_path)
        else:
            logging.warning(f"Downloaded file not found: {file_path}")
            
    else:
        logging.error(f"Invalid resource configuration: {resource}")

def process_all_resources(config_file: Path) -> None:
    """Load resources configuration and process each resource.
    
    Args:
        config_file: Path to the JSON configuration file.
    """
    try:
        resources = load_config(config_file)
        logging.info(f"Processing {len(resources)} resources")
        
        for i, resource in enumerate(resources, 1):
            logging.info(f"Processing resource {i}/{len(resources)}")
            handle_resource(resource)
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to process resources: {e}")
        raise

def split_large_blocklists(input_directory: Path, output_directory: Path, max_lines: int) -> None:
    """Split large blocklist files if they exceed a given number of lines.
    
    Renames files according to the pattern `name-aa.txt`, `name-ab.txt`, etc.
    
    Args:
        input_directory: Directory containing source files.
        output_directory: Directory to write split files to.
        max_lines: Maximum number of lines per output file.
    """
    processed_files = 0
    
    for file_path in input_directory.iterdir():
        if not (file_path.is_file() and file_path.suffix == ".txt"):
            continue
            
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            line_count = len(lines)
            base_name = file_path.stem

            if line_count <= max_lines:
                # Single file, rename with -aa suffix
                new_file_name = f"{base_name}-aa.txt"
                output_file_path = output_directory / new_file_name
                
                with output_file_path.open("w", encoding="utf-8") as output_file:
                    output_file.writelines(lines)
            else:
                # Split into multiple files
                alphabet = string.ascii_lowercase
                part_index = 0
                start_line = 0

                while start_line < line_count:
                    end_line = min(start_line + max_lines, line_count)
                    
                    # Generate suffix (aa, ab, ac, ...)
                    part_suffix = (
                        f"{alphabet[part_index // 26]}"
                        f"{alphabet[part_index % 26]}"
                    )
                    part_file_name = f"{base_name}-{part_suffix}.txt"
                    part_file_path = output_directory / part_file_name
                    
                    with part_file_path.open("w", encoding="utf-8") as part_file:
                        part_file.writelines(lines[start_line:end_line])
                    
                    start_line += max_lines
                    part_index += 1
                    
            processed_files += 1
            
        except OSError as e:
            logging.error(f"Error processing file {file_path}: {e}")

    logging.info(
        f"Processed {processed_files} files, split into chunks of {max_lines} lines"
    )

def merge_all_blocklists(blocklist_directory: Path, output_file: Path) -> None:
    """Merge all blocklist files into a single file, ensuring all IPs are unique.
    
    Args:
        blocklist_directory: Directory containing blocklist files.
        output_file: Path for the merged output file.
    """
    ip_set = set()
    processed_files = 0

    # Collect all IPs from the blocklist files
    for file_path in blocklist_directory.iterdir():
        if not (file_path.is_file() and file_path.suffix == ".txt"):
            continue
            
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    ip = line.strip()
                    if ip and is_valid_ip(ip):
                        ip_set.add(ip)
                        
            processed_files += 1
            
        except OSError as e:
            logging.error(f"Error reading file {file_path}: {e}")

    # Write the unique IPs to the output file
    try:
        with output_file.open("w", encoding="utf-8") as f:
            for ip in sorted(ip_set, key=ipaddress.ip_address):
                f.write(f"{ip}\n")
                
        logging.info(
            f"Merged {processed_files} files with {len(ip_set)} unique IPs into {output_file}"
        )
        
    except OSError as e:
        logging.error(f"Error writing merged file {output_file}: {e}")
        raise

def main() -> None:
    """Main function to orchestrate the blocklist update process."""
    logging.info("Starting blocklist update process")
    
    try:
        clear_directory(BLOCKLISTS_DIR)
        process_all_resources(CONFIG_FILE)
        split_large_blocklists(
            BLOCKLISTS_DIR, 
            BLOCKLISTS_SPLIT_DIR, 
            MAX_LINES_PER_FILE
        )
        merge_all_blocklists(BLOCKLISTS_DIR, BLOCKLISTS_MERGED_FILE_PATH)
        
        logging.info("Blocklist update process completed successfully")
        
    except Exception as e:
        logging.error(f"Blocklist update process failed: {e}")
        raise


if __name__ == "__main__":
    main()
