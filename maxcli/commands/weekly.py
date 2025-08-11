"""Weekly summary command for MaxCLI."""

import subprocess
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import Set, List, Dict, Tuple

def parse_commit_message(message: str) -> (str, str):
    """Parse a commit message to extract its type and a clean summary."""
    match = re.match(r"^(\w+)(?:\([^)]+\))?!?:\s*(.*)", message)
    if match:
        commit_type, summary = match.groups()
        return commit_type.lower(), summary.strip()
    
    # If no conventional commit format, use a generic type
    return "other", message.strip().split('\n')[0]

def get_git_user_email() -> str:
    """Get the user's git email address for filtering commits."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def find_git_repositories(base_path: str) -> List[Path]:
    """Find all git repositories in the given base path."""
    repositories = []
    base_path_obj = Path(base_path).expanduser()
    
    if not base_path_obj.exists():
        print(f"Warning: Base path {base_path} does not exist")
        return repositories
    
    # Look for .git directories in immediate subdirectories
    for item in base_path_obj.iterdir():
        if item.is_dir():
            git_dir = item / ".git"
            if git_dir.exists():
                repositories.append(item)
    
    return repositories

def get_all_branches(repo_path: Path) -> List[str]:
    """Get all branches (local and remote) for a repository."""
    try:
        # Get all local and remote branches
        result = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "-a"],
            capture_output=True,
            text=True,
            check=True
        )
        
        branches = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Clean up branch names (remove * and remotes/origin/ prefix)
                branch = line.strip().lstrip('* ')
                if branch.startswith('remotes/origin/'):
                    branch = branch.replace('remotes/origin/', '')
                # Skip HEAD references
                if 'HEAD' not in branch and branch not in branches:
                    branches.append(branch)
        
        return branches
    except subprocess.CalledProcessError:
        return []

def get_commits_from_repository(repo_path: Path, user_email: str, since_date: str) -> Set[Tuple[str, str, str]]:
    """
    Get all commits from a repository across all branches for the user.
    
    Returns:
        Set of tuples (commit_hash, repo_name, commit_message) to avoid duplicates
    """
    commits = set()
    repo_name = repo_path.name
    
    try:
        # Get all branches
        branches = get_all_branches(repo_path)
        
        for branch in branches:
            try:
                # Use git log to get commits from this branch
                # Format: hash%tab%message
                result = subprocess.run([
                    "git", "-C", str(repo_path), "log",
                    f"--since={since_date}",
                    f"--author={user_email}",
                    "--pretty=format:%H%x09%s",
                    branch
                ], capture_output=True, text=True, check=True)
                
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split('\t', 1)
                        if len(parts) == 2:
                            commit_hash, message = parts
                            # Add to set (automatically deduplicates by hash)
                            commits.add((commit_hash, repo_name, message))
                            
            except subprocess.CalledProcessError:
                # Branch might not exist locally or other git error, skip this branch
                continue
                
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not process repository {repo_name}: {e}")
    
    return commits

def perform_thorough_search(base_path: str, since_date: str) -> str:
    """
    Perform thorough local git search across all repositories.
    
    Args:
        base_path: Path to directory containing git repositories
        since_date: Date string in YYYY-MM-DD format
        
    Returns:
        Raw commit data in the same format as GitHub search
    """
    user_email = get_git_user_email()
    if not user_email:
        return "Error: Could not determine git user email. Please ensure git is configured."
    
    print(f"🔍 Searching for commits by {user_email} since {since_date}")
    print(f"📁 Scanning repositories in: {base_path}")
    
    repositories = find_git_repositories(base_path)
    if not repositories:
        return f"No git repositories found in {base_path}"
    
    print(f"📦 Found {len(repositories)} repositories: {', '.join([r.name for r in repositories])}")
    
    all_commits = set()
    
    for repo_path in repositories:
        print(f"   🔍 Scanning {repo_path.name}...")
        repo_commits = get_commits_from_repository(repo_path, user_email, since_date)
        all_commits.update(repo_commits)
        print(f"      Found {len(repo_commits)} unique commits")
    
    print(f"✅ Total unique commits found: {len(all_commits)}")
    
    # Convert to the same format as GitHub search output
    # Format: repo_name\tcommit_hash\tmessage
    output_lines = []
    for commit_hash, repo_name, message in sorted(all_commits, key=lambda x: x[1]):  # Sort by repo name
        output_lines.append(f"{repo_name}\t{commit_hash}\t{message}")
    
    return '\n'.join(output_lines)

def generate_summary(raw_commits: str) -> str:
    """Generate a human-readable summary from raw commit data."""
    projects = defaultdict(lambda: defaultdict(list))
    
    for line in raw_commits.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        repo, _, message = parts[0], parts[1], parts[2]
        
        commit_type, clean_message = parse_commit_message(message)
        projects[repo][commit_type].append(clean_message)

    summary = "Good morning! Here's a summary of my work from the past week:\n"

    type_map = {
        'feat': 'Features & Enhancements',
        'fix': 'Fixes',
        'refactor': 'Refactoring',
        'docs': 'Documentation',
        'chore': 'Chores & Maintenance',
        'test': 'Tests',
        'other': 'Other Changes'
    }

    for repo, types in projects.items():
        summary += f"\n### Project: {repo}\n"
        for commit_type, messages in types.items():
            if messages:
                title = type_map.get(commit_type, 'Other Changes')
                summary += f"\n*   **{title}:**\n"
                for msg in messages:
                    summary += f"    *   {msg}\n"
    
    return summary

def _get_ai_summary(raw_commits: str) -> str:
    """Generate an AI-powered summary using the Gemini CLI."""
    try:
        # Craft a prompt for summarization
        prompt = "Summarize the following Git commit messages into a concise, human-readable format suitable for a stand-up meeting. Group by project and type of change (e.g., features, fixes, refactors). Focus on key accomplishments and impact.\n\n" + raw_commits
        
        # Execute gemini CLI command
        command = ["gemini", "-p", prompt]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except FileNotFoundError:
        return "Error: 'gemini' command not found. Please ensure the Gemini CLI is installed and in your PATH."
    except subprocess.CalledProcessError as e:
        return f"Error executing 'gemini' command: {e.stderr}"

def weekly_summary_command(args):
    """Generate a weekly summary of commits."""
    try:
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
        
        # Use thorough local search if requested
        if args.thorough:
            search_path = getattr(args, 'path', '~/developer/urbansharing')
            print(f"🔍 Performing thorough local search...")
            raw_commits = perform_thorough_search(search_path, start_date)
        else:
            # Use GitHub CLI search (original behavior)
            command = [
                "gh", "search", "commits",
                f"--committer-date", f">{start_date}",
                "--author", "@me",
                "--limit", str(args.limit)
            ]
            
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            raw_commits = result.stdout

        if args.ai:
            print("Generating AI summary with Gemini CLI...")
            output = _get_ai_summary(raw_commits)
        elif args.raw:
            output = raw_commits
        else:
            output = generate_summary(raw_commits)

        if args.save:
            summary_file = args.save
            # Ensure the directory exists
            save_dir = os.path.dirname(summary_file)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            with open(summary_file, "w") as f:
                f.write(output)
            print(output)
            print(f"Weekly summary has been saved to {summary_file}")
        else:
            print(output)
        
    except FileNotFoundError as e:
        if args.thorough:
            print("Error: Git command not found. Please ensure git is installed and in your PATH.")
        else:
            print("Error: 'gh' command not found. Please ensure the GitHub CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        if args.thorough:
            print(f"Error executing git command: {e.stderr}")
        else:
            print(f"Error executing 'gh' command: {e.stderr}")
