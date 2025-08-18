"""Git push script for automated blocklist updates in CI environment."""

import logging, subprocess, sys
from pathlib import Path

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run_git_command(cmd: list, description: str) -> None:
    """Run a git command with proper error handling."""
    try:
        logging.info(f"{description}...")
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.stdout.strip():
            logging.info(f"Output: {result.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(cmd)}")
        logging.error(f"Exit code: {e.returncode}")
        if e.stdout:
            logging.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logging.error(f"Stderr: {e.stderr}")
        raise
    except subprocess.TimeoutExpired:
        logging.error(f"Command timed out: {' '.join(cmd)}")
        raise


def add_gitignore_entries() -> None:
    """Add necessary entries to .gitignore."""
    gitignore_path = Path(".gitignore")
    gitignore_entries = [".gitignore", "venv_blocklist/", "maxmind/"]
    
    try:
        with gitignore_path.open("a", encoding="utf-8") as f:
            for entry in gitignore_entries:
                f.write(f"{entry}\n")
        logging.info("Updated .gitignore")
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
        
        # Configure git user (required for CI)
        run_git_command(
            ["git", "config", "user.email", commit_email],
            "Setting git user email"
        )
        run_git_command(
            ["git", "config", "user.name", commit_author],
            "Setting git user name"
        )
        
        # Add existing files/directories
        paths_added = []
        for path in paths_to_add:
            if Path(path).exists():
                run_git_command(
                    ["git", "add", path],
                    f"Adding {path}"
                )
                paths_added.append(path)
            else:
                logging.debug(f"Path does not exist, skipping: {path}")
        
        # Check if there are changes to commit
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if not result.stdout.strip():
                logging.info("No changes to commit")
                return
                
            changed_files = result.stdout.strip().split('\n')
            logging.info(f"Found {len(changed_files)} changed files")
            for file in changed_files[:10]:  # Show first 10
                logging.info(f"  - {file}")
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to check git status: {e}")
            return
        
        # Create commit
        run_git_command(
            ["git", "commit", "-m", commit_message],
            "Creating commit"
        )
        
        # Set remote URL
        run_git_command(
            ["git", "remote", "set-url", "origin", repo_url],
            "Setting remote URL"
        )
        
        # Push to remote
        run_git_command(
            ["git", "push", "origin", f"HEAD:{branch_name}"],
            "Pushing to remote"
        )
        
        logging.info("Push completed successfully")
        
    except Exception as e:
        logging.error(f"Git operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()