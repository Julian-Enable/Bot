#!/usr/bin/env python3
"""Non-intrusive script to update a file and push a commit using a PAT to the default branch.

This script writes a timestamped line to individual files in the contributions folder
and pushes to the default branch (default `master`) so the commits count as contributions on GitHub.

Multiple runs per day create separate files to avoid conflicts.
Each execution makes 2-5 random commits to vary daily totals (25-50 commits per day).

Environment variables expected (set by the workflow):
- PAT: personal access token with repo permissions
- COMMIT_NAME: the name to use as commit author
- COMMIT_EMAIL: the email to use as commit author (must be associated with your GitHub account)
- GITHUB_REPOSITORY: owner/repo
- BOT_BRANCH (optional): branch to use for bot commits (default: master)
"""
import os
import subprocess
import random
from pathlib import Path
from datetime import datetime, timezone
import time


def run(cmd):
    print('>',' '.join(cmd))
    result = subprocess.run(cmd, check=True)
    return result


repo = os.environ.get('GITHUB_REPOSITORY')
if not repo:
    raise SystemExit('GITHUB_REPOSITORY is required')

pat = os.environ.get('PAT')
if not pat:
    raise SystemExit('PAT secret is required. Create a repo secret named PAT with a personal access token.')

name = os.environ.get('COMMIT_NAME')
email = os.environ.get('COMMIT_EMAIL')
if not name or not email:
    raise SystemExit('COMMIT_NAME and COMMIT_EMAIL secrets are required and must match your GitHub account.')

# Use the default branch so commits count as contributions on GitHub
branch = os.environ.get('BOT_BRANCH', 'master')

# Configure git author locally
run(['git', 'config', 'user.name', name])
run(['git', 'config', 'user.email', email])

# Set up remote with PAT
push_url = f'https://x-access-token:{pat}@github.com/{repo}.git'
run(['git', 'remote', 'set-url', 'origin', push_url])

# Fetch latest from remote
run(['git', 'fetch', 'origin'])

# Try to checkout existing remote branch or create new one
try:
    run(['git', 'checkout', branch])
    # If branch exists, pull latest changes
    run(['git', 'pull', 'origin', branch, '--no-rebase'])
except subprocess.CalledProcessError:
    # Branch doesn't exist locally, create it
    try:
        run(['git', 'checkout', '-b', branch, f'origin/{branch}'])
    except subprocess.CalledProcessError:
        # Remote branch doesn't exist either, create new branch
        run(['git', 'checkout', '-b', branch])

# Random number of commits per execution (2-3) to vary daily totals
# 15 executions × 2-3 commits = 30-45 commits per day
num_commits = random.randint(2, 3)
print(f'Creating {num_commits} commits for this execution...')

p = Path('contributions')
for i in range(num_commits):
    # Create unique file for each commit to avoid conflicts
    # Format: YYYY/MM/DD/HH-MM-SS-N.md
    now_dt = datetime.now(timezone.utc)
    year_dir = p / str(now_dt.year)
    month_dir = year_dir / f"{now_dt.month:02d}"
    day_dir = month_dir / f"{now_dt.day:02d}"
    day_dir.mkdir(parents=True, exist_ok=True)

    # Create unique file for this commit
    filename = f"{now_dt.hour:02d}-{now_dt.minute:02d}-{now_dt.second:02d}-{i+1}.md"
    f = day_dir / filename
    now = now_dt.isoformat().replace('+00:00', 'Z')
    content = f"# Activity Log\n\nTimestamp: {now}\nCommit: {i+1}/{num_commits}\n\nThis is an automated commit to maintain contribution activity.\n"

    # Write the file (each execution creates a new file, no conflicts)
    f.write_text(content, encoding='utf-8')

    # git add/commit
    run(['git', 'add', str(f)])
    msg = f'chore: contribution update {now}'
    run(['git', 'commit', '-m', msg])
    
    # Small delay between commits to ensure unique timestamps
    if i < num_commits - 1:
        time.sleep(2)

# Push all commits at once
try:
    run(['git', 'push', 'origin', f'{branch}:{branch}'])
except subprocess.CalledProcessError:
    # If push fails due to concurrent update, pull and try again
    print('Push failed, pulling latest changes and retrying...')
    run(['git', 'pull', 'origin', branch, '--no-rebase', '--strategy=recursive', '--strategy-option=theirs'])
    run(['git', 'push', 'origin', f'{branch}:{branch}'])

