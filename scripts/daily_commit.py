#!/usr/bin/env python3
"""Non-intrusive script to update a file and push a commit using a PAT.

Writes a timestamped line in contributions/YYYY/MM/DD/ and pushes a single
commit per run to the configured branch (default: contrib-bot).

Environment variables expected:
- PAT: personal access token with repo permissions
- COMMIT_NAME: commit author name
- COMMIT_EMAIL: commit author email (must match your GitHub account)
- GITHUB_REPOSITORY: owner/repo
- BOT_BRANCH: branch for bot commits (default: contrib-bot)
"""

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_RETRIES = 3


def run(cmd):
    """Run a git command, print command and any error output."""
    print("> ", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip() if result.stderr else result.stdout.strip()
        print(f"  ERROR (code {result.returncode}): {err}", file=sys.stderr, flush=True)
    return result


def run_check(cmd):
    """Run a git command and raise SystemExit on failure."""
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip() if result.stderr else result.stdout.strip()
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{err}")
    return result


def git_config(name, value):
    run_check(["git", "config", name, value])


def setup_remote(repo, pat):
    push_url = f"https://x-access-token:{pat}@github.com/{repo}.git"
    run_check(["git", "remote", "set-url", "origin", push_url])


def checkout_branch(branch):
    """Try to checkout existing branch or create it."""
    r = run(["git", "checkout", branch])
    if r.returncode == 0:
        r = run(["git", "pull", "origin", branch, "--no-rebase"])
        if r.returncode != 0:
            print(f"Pull failed, resetting to origin/{branch}", file=sys.stderr, flush=True)
            run(["git", "fetch", "origin"])
            run(["git", "reset", "--hard", f"origin/{branch}"])
        return

    r = run(["git", "checkout", "-b", branch, f"origin/{branch}"])
    if r.returncode == 0:
        return

    r = run(["git", "checkout", "-b", branch])
    if r.returncode != 0:
        raise SystemExit(f"Could not checkout or create branch '{branch}'")


def count_today(day_dir):
    if day_dir.exists():
        return len(list(day_dir.glob("*.md")))
    return 0


def create_commit(day_dir, n, daily_target, now_dt):
    filename = f"{now_dt.hour:02d}-{now_dt.minute:02d}-{now_dt.second:02d}-{n}.md"
    f = day_dir / filename
    now = now_dt.isoformat().replace("+00:00", "Z")
    content = (
        f"# Activity Log\n\n"
        f"Timestamp: {now}\n"
        f"Commit: {n}/{daily_target}\n\n"
        f"This is an automated commit to maintain contribution activity.\n"
    )
    f.write_text(content, encoding="utf-8")

    r = run(["git", "add", str(f)])
    if r.returncode != 0:
        print(f"  git add failed for {f}", file=sys.stderr, flush=True)
        return False

    msg = f"chore: contribution update {now}"
    r = run(["git", "commit", "-m", msg])
    if r.returncode != 0:
        print(f"  git commit failed for {f}", file=sys.stderr, flush=True)
        return False
    return True


def push_with_retry(branch):
    """Try to push, with fallback pull+push on conflict."""
    for attempt in range(1, MAX_RETRIES + 1):
        r = run(["git", "push", "origin", f"{branch}:{branch}"])
        if r.returncode == 0:
            print(f"  Push succeeded on attempt {attempt}", flush=True)
            return True

        if attempt < MAX_RETRIES:
            print(f"  Push failed (attempt {attempt}), pulling and retrying...", file=sys.stderr, flush=True)
            run(["git", "fetch", "origin"])
            r = run(["git", "pull", "origin", branch, "--no-rebase", "--strategy=recursive", "--strategy-option=theirs"])
            if r.returncode != 0:
                print("  Pull failed, resetting to origin...", file=sys.stderr, flush=True)
                run(["git", "reset", "--hard", f"origin/{branch}"])

    return False


def main():
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY is required")

    pat = os.environ.get("PAT")
    if not pat:
        raise SystemExit("PAT secret is required. Create a repo secret named PAT with a personal access token.")

    name = os.environ.get("COMMIT_NAME")
    email = os.environ.get("COMMIT_EMAIL")
    if not name or not email:
        raise SystemExit("COMMIT_NAME and COMMIT_EMAIL secrets are required.")

    branch = os.environ.get("BOT_BRANCH", "contrib-bot")

    today = datetime.now(timezone.utc)
    day_dir = Path("contributions") / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"

    # Configure git
    git_config("user.name", name)
    git_config("user.email", email)
    setup_remote(repo, pat)

    # Fetch and checkout
    run(["git", "fetch", "origin"])
    checkout_branch(branch)

    # Determine how many commits already exist today
    already_done = count_today(day_dir)
    daily_target = 1  # One commit per run is enough to keep the graph green
    remaining = max(0, daily_target - already_done)

    print(f"Branch: {branch} | Today: {today:%Y-%m-%d} | Already done: {already_done} | Remaining: {remaining}")

    if remaining == 0:
        print("Daily contribution already exists. Nothing to do.")
        sys.exit(0)

    day_dir.mkdir(parents=True, exist_ok=True)

    now_dt = datetime.now(timezone.utc)
    if not create_commit(day_dir, already_done + 1, daily_target, now_dt):
        raise SystemExit("Failed to create commit")

    # Push with retry
    success = push_with_retry(branch)
    if not success:
        print("WARNING: Could not push commits. They exist locally but may not be on GitHub.", file=sys.stderr)
        sys.exit(1)

    print("Done! Contribution recorded.")


if __name__ == "__main__":
    main()
