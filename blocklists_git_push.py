"""Git push script for automated blocklist updates in CI environment."""

import logging
import os
import sys
from pathlib import Path

from git import Repo, Actor
import git

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
        
        # Add gitignore entries
        add_gitignore_entries()
        
        # Initialize repo
        repo = Repo(os.getcwd())
        
        # Configure git for large files
        configure_git_for_large_files(repo)
        
        logging.info("Adding files to staging area...")
        
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
        logging.info(f"Successfully pushed to {branch_name}")

                
    except Exception as e:
        logging.error(f"Git operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()