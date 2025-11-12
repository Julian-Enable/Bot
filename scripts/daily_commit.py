#!/usr/bin/env python3
"""Non-intrusive script to update a file and push a commit using a PAT to a dedicated branch.

This script writes a timestamped line to individual files and pushes to a separate
branch (default `contrib-bot`) so the repository's main branches are not modified.

Multiple runs per day create separate files to avoid conflicts.

Environment variables expected (set by the workflow):
- PAT: personal access token with repo permissions
- COMMIT_NAME: the name to use as commit author
- COMMIT_EMAIL: the email to use as commit author (must be associated with your GitHub account)
- GITHUB_REPOSITORY: owner/repo
- BOT_BRANCH (optional): branch to use for bot commits (default: contrib-bot)
"""
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def run(cmd):
    print('>',' '.join(cmd))
    subprocess.run(cmd, check=True)


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

# Use a dedicated branch so we don't touch default branches
branch = os.environ.get('BOT_BRANCH', 'contrib-bot')

# Create unique file for each execution to avoid conflicts
# Format: YYYY/MM/DD/HH-MM-SS.md
p = Path('contributions')
now_dt = datetime.now(timezone.utc)
year_dir = p / str(now_dt.year)
month_dir = year_dir / f"{now_dt.month:02d}"
day_dir = month_dir / f"{now_dt.day:02d}"
day_dir.mkdir(parents=True, exist_ok=True)

# Create unique file for this execution
filename = f"{now_dt.hour:02d}-{now_dt.minute:02d}-{now_dt.second:02d}.md"
f = day_dir / filename
now = now_dt.isoformat().replace('+00:00', 'Z')
content = f"# Activity Log\n\nTimestamp: {now}\n\nThis is an automated commit to maintain contribution activity.\n"

# Write the file (each execution creates a new file, no conflicts)
f.write_text(content, encoding='utf-8')

# Configure git author locally
run(['git', 'config', 'user.name', name])
run(['git', 'config', 'user.email', email])

# Create or switch to the bot branch (non-destructive for default branches)
run(['git', 'checkout', '-B', branch])

# git add/commit
run(['git', 'add', str(f)])
msg = f'chore: daily contribution update {now}'
run(['git', 'commit', '-m', msg])

# push directly using PAT embedded URL to avoid changing origin permanently
push_url = f'https://x-access-token:{pat}@github.com/{repo}.git'
run(['git', 'push', push_url, f'HEAD:refs/heads/{branch}'])

