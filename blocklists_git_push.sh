#!/bin/bash

ACCESS_TOKEN=$1
COMMIT_MESSAGE="[bot] Update blocklists"
COMMIT_AUTHOR="Maxime Wewer"
COMMIT_EMAIL="MaximeWewer@users.noreply.github.com"
REPO_URL="https://MaximeWewer${ACCESS_TOKEN}@github.com/MaximeWewer/HeimdallBlocklists.git"
BRANCH_NAME="main"

BLOCKLISTS_DIR="./blocklists"
BLOCKLISTS_SPLIT_DIR="./blocklists_split"
STATISTICS_DIR="./statistics"

# Add gitignore
echo ".gitignore" >> .gitignore
echo "venv_blocklist/" >> .gitignore
echo "maxmind/" >> .gitignore 

# Set identity of the commiter
git config --global user.email "$COMMIT_EMAIL"
git config --global user.name "$COMMIT_AUTHOR"

# Add results
git add $BLOCKLISTS_DIR $BLOCKLISTS_SPLIT_DIR $STATISTICS_DIR

# Commit the changes
git commit -m "$COMMIT_MESSAGE"

# Push the changes to the repository
git push "$REPO_URL" HEAD:"$BRANCH_NAME"
