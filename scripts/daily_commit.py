#!/usr/bin/env python3
"""Non-intrusive script to update a file and push a commit using a PAT to the default branch.

This script writes a timestamped line to individual files in the contributions folder
and pushes to the default branch (default `master`) so the commits count as contributions on GitHub.

The workflow may run several times per day, but the script self-limits the daily total.
At the start it derives a target number of commits for the day (a stable random value
between 1 and 50, seeded by the UTC date), counts how many commits already exist for
today, and only creates the remaining ones. This makes the daily total highly variable
(e.g. one day 1, another 25, another 40) while never going below 1 or above 50.

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

# Daily target: a stable random value between 1 and 50, seeded by the UTC date,
# so every run on the same day agrees on the same target.
today = datetime.now(timezone.utc)
day_dir = Path('contributions') / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"
daily_target = random.Random(f'{repo}:{today:%Y-%m-%d}').randint(1, 50)

# How many commits already exist for today (files created by earlier runs).
already_done = len(list(day_dir.glob('*.md'))) if day_dir.exists() else 0
remaining = max(0, daily_target - already_done)
print(f"Daily target: {daily_target}, already done today: {already_done}, remaining: {remaining}")

if remaining == 0:
    print('Daily target already reached. Nothing to do.')
    raise SystemExit(0)

day_dir.mkdir(parents=True, exist_ok=True)
for i in range(remaining):
    # Unique file per commit. Format: YYYY/MM/DD/HH-MM-SS-N.md
    now_dt = datetime.now(timezone.utc)
    # Number this commit within the whole day so filenames never collide
    # with files created by earlier runs today.
    n = already_done + i + 1
    filename = f"{now_dt.hour:02d}-{now_dt.minute:02d}-{now_dt.second:02d}-{n}.md"
    f = day_dir / filename
    now = now_dt.isoformat().replace('+00:00', 'Z')
    content = f"# Activity Log\n\nTimestamp: {now}\nCommit: {n}/{daily_target}\n\nThis is an automated commit to maintain contribution activity.\n"

    # Write the file (unique name, no conflicts)
    f.write_text(content, encoding='utf-8')

    # git add/commit
    run(['git', 'add', str(f)])
    msg = f'chore: contribution update {now}'
    run(['git', 'commit', '-m', msg])

# Push all commits at once
try:
    run(['git', 'push', 'origin', f'{branch}:{branch}'])
except subprocess.CalledProcessError:
    # If push fails due to concurrent update, pull and try again
    print('Push failed, pulling latest changes and retrying...')
    run(['git', 'pull', 'origin', branch, '--no-rebase', '--strategy=recursive', '--strategy-option=theirs'])
    run(['git', 'push', 'origin', f'{branch}:{branch}'])

