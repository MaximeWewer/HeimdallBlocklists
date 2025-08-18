#!/usr/bin/env python3

import sys, os
from pathlib import Path
from git import Repo, Actor

def main():
    if len(sys.argv) != 2:
        print("Usage: python blocklists_git_push.py <ACCESS_TOKEN>", file=sys.stderr)
        sys.exit(1)
    
    access_token = sys.argv[1]
    commit_message = "[bot] Update blocklists"
    commit_author = "Maxime Wewer"
    commit_email = "MaximeWewer@users.noreply.github.com"
    repo_url = f"https://MaximeWewer{access_token}@github.com/MaximeWewer/HeimdallBlocklists.git"
    branch_name = "main"
    
    blocklists_dir = "./blocklists"
    blocklists_split_dir = "./blocklists_split"
    statistics_dir = "./statistics"
    readme = "README.md"
    
    # Add gitignore entries
    gitignore_path = Path(".gitignore")
    gitignore_entries = [".gitignore", "venv_blocklist/", "maxmind/"]
    
    with gitignore_path.open("a", encoding="utf-8") as f:
        for entry in gitignore_entries:
            f.write(f"{entry}\n")
    
    # Initialize repo
    repo = Repo(os.getcwd())
    
    # Add results
    repo.index.add([blocklists_dir, blocklists_split_dir, statistics_dir, readme])
    
    # Create actor for commit (no need for global config in CI)
    actor = Actor(commit_author, commit_email)
    
    # Commit the changes
    repo.index.commit(commit_message, author=actor, committer=actor)
    
    # Push the changes to the repository
    origin = repo.remote("origin")
    origin.set_url(repo_url)
    origin.push(f"HEAD:{branch_name}")

if __name__ == "__main__":
    main()