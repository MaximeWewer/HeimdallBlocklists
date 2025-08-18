"""Update README.md with blocklist URLs from the generated files."""
import logging
import re
from pathlib import Path
from typing import List

# Setup logger
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
BLOCKLIST_DIR: Path = Path("./blocklists")
SPLIT_BLOCKLIST_DIR: Path = Path("./blocklists_split")
README_FILE: Path = Path("README.md")
GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main"

def extract_urls(directory: Path) -> List[str]:
    """Extract URLs from .txt files in the given directory.
    
    Args:
        directory: Path to the directory containing .txt files.
        
    Returns:
        List of GitHub raw URLs for the .txt files.
    """
    txt_files = list(directory.glob("*.txt"))
    logging.debug(f"Found {len(txt_files)} .txt files in {directory}")
    
    return [
        f"{GITHUB_RAW_BASE_URL}/{directory.name}/{filename.name}"
        for filename in txt_files
    ]

def update_readme(blocklist_urls: List[str], split_blocklist_urls: List[str]) -> None:
    """Update the README.md file with the new blocklist URLs.
    
    Args:
        blocklist_urls: List of URLs for main blocklist files.
        split_blocklist_urls: List of URLs for split blocklist files.
    """
    try:
        with README_FILE.open("r", encoding="utf-8") as file:
            content = file.read()
    except OSError as e:
        logging.error(f"Error reading README file: {e}")
        raise

    # Sort URLs for consistent ordering
    blocklist_urls.sort()
    split_blocklist_urls.sort()
    
    logging.info(f"Updating README with {len(blocklist_urls)} main and {len(split_blocklist_urls)} split URLs")

    # Format URL sections
    blocklist_urls_text = "```text\n" + "\n".join(blocklist_urls) + "\n```\n"
    split_blocklist_urls_text = "```text\n" + "\n".join(split_blocklist_urls) + "\n```\n"

    # Replace the blocklists URLs section
    updated_content = re.sub(
        r"(## Blocklists URLs.*?)(## Contributions)",
        (
            "## Blocklists URLs\n\n"
            "Here are the URLs for the community blocklists:\n\n"
            f"{blocklist_urls_text}\n"
            "Here are the URLs for the split versions:\n\n"
            f"{split_blocklist_urls_text}\n"
            "## Contributions"
        ),
        content,
        flags=re.DOTALL
    )
    
    if updated_content == content:
        logging.warning("No changes made to README - check the section markers")
        return

    try:
        with README_FILE.open("w", encoding="utf-8") as file:
            file.write(updated_content)
        logging.info("README.md URLs updated successfully")
    except OSError as e:
        logging.error(f"Error writing README file: {e}")
        raise

def main() -> None:
    """Main function to update README with blocklist URLs."""
    logging.info("Starting README URL update process")
    
    try:
        # Validate directories exist
        if not BLOCKLIST_DIR.exists():
            logging.error(f"Blocklist directory does not exist: {BLOCKLIST_DIR}")
            return
        if not SPLIT_BLOCKLIST_DIR.exists():
            logging.error(f"Split blocklist directory does not exist: {SPLIT_BLOCKLIST_DIR}")
            return
        if not README_FILE.exists():
            logging.error(f"README file does not exist: {README_FILE}")
            return
            
        # Extract URLs from both directories
        blocklist_urls = extract_urls(BLOCKLIST_DIR)
        split_blocklist_urls = extract_urls(SPLIT_BLOCKLIST_DIR)
        
        if not blocklist_urls and not split_blocklist_urls:
            logging.warning("No blocklist files found to generate URLs")
            return
            
        # Update README with new URLs
        update_readme(blocklist_urls, split_blocklist_urls)
        
        logging.info("README URL update completed successfully")
        
    except Exception as e:
        logging.error(f"README URL update failed: {e}")
        raise


if __name__ == "__main__":
    main()
