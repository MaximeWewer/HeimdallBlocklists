"""Git push script for automated blocklist updates in CI environment."""

import logging
import os
import sys
from pathlib import Path

from git import Repo, Actor

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def configure_git_for_large_files(repo: Repo) -> None:
    """Configure Git settings for handling large files and CI environment."""
    with repo.config_writer() as config:
        # Increase buffer sizes for large files
        config.set_value("http", "postBuffer", "524288000")  # 500MB
        config.set_value("http", "maxRequestBuffer", "100M")
        config.set_value("core", "compression", "0")  # Disable compression
        config.set_value("pack", "windowMemory", "100M")
        config.set_value("pack", "packSizeLimit", "100M")
        config.set_value("pack", "threads", "1")  # Single thread for CI stability
        

def add_gitignore_entries() -> None:
    """Add necessary entries to .gitignore."""
    gitignore_path = Path(".gitignore")
    gitignore_entries = [".gitignore", "venv_blocklist/", "maxmind/"]
    
    try:
        with gitignore_path.open("a", encoding="utf-8") as f:
            for entry in gitignore_entries:
                f.write(f"{entry}\n")
    except OSError as e:
        logging.warning(f"Could not update .gitignore: {e}")


def analyze_file_sizes(paths_to_add: list) -> None:
    """Analyze and log file sizes before git operations."""
    logging.info("Analyzing file sizes before git operations...")
    
    total_size = 0
    large_files = []
    
    for path_str in paths_to_add:
        path = Path(path_str)
        
        if not path.exists():
            logging.warning(f"Path does not exist: {path}")
            continue
            
        if path.is_file():
            size = path.stat().st_size
            size_mb = size / (1024 * 1024)
            total_size += size
            
            logging.info(f"File: {path} - Size: {size_mb:.2f} MB")
            
            # Flag files larger than 50MB
            if size_mb > 50:
                large_files.append((path, size_mb))
                
        elif path.is_dir():
            dir_size = 0
            file_count = 0
            
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    dir_size += file_size
                    file_count += 1
                    
                    # Log individual large files in directories
                    file_size_mb = file_size / (1024 * 1024)
                    if file_size_mb > 50:
                        large_files.append((file_path, file_size_mb))
                        logging.warning(f"Large file detected: {file_path} - Size: {file_size_mb:.2f} MB")
            
            dir_size_mb = dir_size / (1024 * 1024)
            total_size += dir_size
            
            logging.info(f"Directory: {path} - Files: {file_count} - Total Size: {dir_size_mb:.2f} MB")
    
    total_size_mb = total_size / (1024 * 1024)
    logging.info(f"Total size to push: {total_size_mb:.2f} MB")
    
    # Warn about large files
    if large_files:
        logging.warning(f"Found {len(large_files)} files larger than 50MB:")
        for file_path, size_mb in large_files:
            logging.warning(f"  - {file_path}: {size_mb:.2f} MB")
        
        # GitHub has a 100MB limit per file
        huge_files = [(f, s) for f, s in large_files if s > 100]
        if huge_files:
            logging.error("Files larger than 100MB detected (GitHub limit):")
            for file_path, size_mb in huge_files:
                logging.error(f"  - {file_path}: {size_mb:.2f} MB")
            logging.error("These files may cause push failures!")
    
    # Warn about total size
    if total_size_mb > 1000:  # 1GB
        logging.warning(f"Total push size is large: {total_size_mb:.2f} MB - this may take time or fail")
    elif total_size_mb > 500:  # 500MB
        logging.info(f"Moderate push size: {total_size_mb:.2f} MB - monitoring recommended")


def main() -> None:
    """Main function to handle git operations for blocklist updates."""
    if len(sys.argv) != 2:
        logging.error("Usage: python blocklists_git_push.py <ACCESS_TOKEN>")
        sys.exit(1)
    
    access_token = sys.argv[1]
    commit_message = "[bot] Update blocklists"
    commit_author = "Maxime Wewer"
    commit_email = "MaximeWewer@users.noreply.github.com"
    repo_url = f"https://MaximeWewer{access_token}@github.com/MaximeWewer/HeimdallBlocklists.git"
    branch_name = "main"
    
    # Paths to add
    paths_to_add = [
        "./blocklists",
        "./blocklists_split", 
        "./statistics",
        "README.md"
    ]
    
    try:
        logging.info("Starting git push process")
        
        # Analyze file sizes before git operations
        analyze_file_sizes(paths_to_add)
        
        # Add gitignore entries
        add_gitignore_entries()
        
        # Initialize repo
        repo = Repo(os.getcwd())
        
        # Configure git for large files
        configure_git_for_large_files(repo)
        
        # Add files individually to handle large files better
        for path in paths_to_add:
            if Path(path).exists():
                try:
                    repo.index.add([path])
                    logging.info(f"Added {path}")
                except Exception as e:
                    logging.warning(f"Could not add {path}: {e}")
            else:
                logging.warning(f"Path does not exist: {path}")
        
        # Check if there are changes to commit
        if not repo.index.diff("HEAD"):
            logging.info("No changes to commit")
            return
        
        logging.info("Creating commit...")
        # Create actor for commit
        actor = Actor(commit_author, commit_email)
        
        # Commit the changes
        repo.index.commit(commit_message, author=actor, committer=actor)
        
        logging.info("Pushing to remote...")
        origin = repo.remote("origin")
        origin.set_url(repo_url)
        origin.push(f"HEAD:{branch_name}")
                
    except Exception as e:
        logging.error(f"Git operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()