"""Git push script for automated blocklist updates in CI environment."""

import logging
import sys
from pathlib import Path

from git import Repo, Actor

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
    
    # Paths to add (only existing ones will be added)
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
        repo = Repo(".")
        
        logging.info("Adding files to staging area...")
        
        # Add existing files/directories
        paths_added = []
        for path in paths_to_add:
            if Path(path).exists():
                repo.index.add([path])
                paths_added.append(path)
                logging.info(f"Added {path}")
            else:
                logging.debug(f"Path does not exist, skipping: {path}")
        
        # Check if there are changes to commit
        staged_changes = list(repo.index.diff("HEAD"))
        if not staged_changes:
            logging.info("No changes to commit")
            return
        
        logging.info(f"Found {len(staged_changes)} staged changes")
        
        # Create commit
        logging.info("Creating commit...")
        actor = Actor(commit_author, commit_email)
        repo.index.commit(commit_message, author=actor, committer=actor)
        
        # Push to remote
        logging.info("Pushing to remote...")
        origin = repo.remote("origin")
        origin.set_url(repo_url)
        origin.push(f"HEAD:{branch_name}")
        
    except Exception as e:
        logging.error(f"Git operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()