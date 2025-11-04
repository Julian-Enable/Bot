#!/usr/bin/env python3
"""Non-intrusive script to update a file and push a commit using a PAT to a dedicated branch.

This script writes a timestamped line to `contributions/keep_alive.md` and pushes to a separate
branch (default `contrib-bot`) so the repository's main branches are not modified.

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

# prepare file
p = Path('contributions')
p.mkdir(exist_ok=True)
f = p / 'keep_alive.md'
now_dt = datetime.now(timezone.utc)
now = now_dt.isoformat().replace('+00:00', 'Z')
line = f'- {now}\n'

# avoid duplicate commits on the same UTC day
if f.exists():
    text = f.read_text(encoding='utf-8')
    lines = [l for l in text.splitlines() if l.strip()]
    if lines:
        last = lines[-1]
        if last.startswith('- '):
            ts = last[2:].strip()
            try:
                # handle ISO Z suffix
                if ts.endswith('Z'):
                    ts = ts.rstrip('Z')
                last_dt = datetime.fromisoformat(ts)
                if last_dt.date() == now_dt.date():
                    print('No commit: already committed today (UTC).')
                    raise SystemExit(0)
            except Exception:
                # if parsing fails, continue and append anyway
                pass
    text = text + line
    f.write_text(text, encoding='utf-8')
else:
    f.write_text(line, encoding='utf-8')

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

