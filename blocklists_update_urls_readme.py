import re
import logging
from pathlib import Path
from typing import List

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

blocklist_dir: Path = Path('blocklists')
split_blocklist_dir: Path = Path('blocklists_split')
readme_file: Path = Path('README.md')

def extract_urls(directory: Path) -> List[str]:
    """
    Extracts URLs from .txt files.
    """
    return [f'https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/{directory.name}/{filename.name}' for filename in directory.glob('*.txt')]

def update_readme(blocklist_urls: List[str], split_blocklist_urls: List[str]) -> None:
    """
    Updates the README.md file with the new blocklists URLs.
    """
    with open(readme_file, 'r') as file:
        content: str = file.read()

    blocklist_urls_text: str = '```text\n' + '\n'.join(blocklist_urls) + '\n```\n'
    split_blocklist_urls_text: str = '```text\n' + '\n'.join(split_blocklist_urls) + '\n```\n'

    updated_content: str = re.sub(
        r'(## Blocklists URLs.*?)(## Contributions)',
        (f'## Blocklists URLs\n\n'
         f'Here are the URLs for the community blocklists:\n\n{blocklist_urls_text}\n'
         f'Here are the URLs for the split versions:\n\n{split_blocklist_urls_text}\n'
         f'## Contributions'),
        content, flags=re.DOTALL
    )

    with open(readme_file, 'w') as file:
        file.write(updated_content)

    logging.info("URLs of README.md updated.")

if __name__ == "__main__":
    blocklist_urls: List[str] = extract_urls(blocklist_dir)
    split_blocklist_urls: List[str] = extract_urls(split_blocklist_dir)
    update_readme(blocklist_urls, split_blocklist_urls)
