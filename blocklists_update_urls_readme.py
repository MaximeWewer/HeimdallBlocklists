import os
import re

# Chemins des fichiers de blocklists
blocklist_dir = 'blocklists'
split_blocklist_dir = 'blocklists_split'
readme_file = 'README.md'

def extract_urls(directory):
    urls = []
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            # Ajouter l'URL pour chaque fichier .txt trouvé
            urls.append(f'https://raw.githubusercontent.com/MaximeWewer/HeimdallBlocklists/main/{directory}/{filename}')
    return urls

def update_readme(blocklist_urls, split_blocklist_urls):
    with open(readme_file, 'r') as file:
        content = file.read()

    # Regex pour trouver les sections des blocklists
    content = re.sub(r'## Blocklists URLs\n\n.*?(?=\n\n)', 
                     f'## Blocklists URLs\n\nHere are the URLs for the community blocklists and their split versions:\n\n' +
                     '\n'.join(blocklist_urls) + '\n\n' +
                     '\n'.join(split_blocklist_urls),
                     content, flags=re.DOTALL)

    with open(readme_file, 'w') as file:
        file.write(content)

if __name__ == "__main__":
    blocklist_urls = extract_urls(blocklist_dir)
    split_blocklist_urls = extract_urls(split_blocklist_dir)
    update_readme(blocklist_urls, split_blocklist_urls)
