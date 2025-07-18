"""Weekly summary command for MaxCLI."""

import subprocess
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict

def parse_commit_message(message: str) -> (str, str):
    """Parse a commit message to extract its type and a clean summary."""
    match = re.match(r"^(\w+)(?:\([^)]+\))?!?:\s*(.*)", message)
    if match:
        commit_type, summary = match.groups()
        return commit_type.lower(), summary.strip()
    
    # If no conventional commit format, use a generic type
    return "other", message.strip().split('\n')[0]

def generate_summary(raw_commits: str) -> str:
    """Generate a human-readable summary from raw commit data."""
    projects = defaultdict(lambda: defaultdict(list))
    
    for line in raw_commits.strip().split('\n'):
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        repo, _, message = parts[0], parts[1], parts[2]
        
        commit_type, clean_message = parse_commit_message(message)
        projects[repo][commit_type].append(clean_message)

    summary = "Good morning! Here’s a summary of my work from the past week:\n"

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
        
    except FileNotFoundError:
        print("Error: 'gh' command not found. Please ensure the GitHub CLI is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'gh' command: {e.stderr}")
