"""
Git Manager Module for MaxCLI.

This module provides simplified Git operations wrapped in easy-to-use commands
that combine multi-step workflows, add safety checks, and provide helpful feedback.
"""

import argparse
from maxcli.commands.git import (
    git_wip_command,
    git_undo_commit_command,
    git_redo_commit_command,
    git_cleanup_branches_command,
    git_track_remote_command,
    git_safe_force_command,
    git_sync_command,
    git_new_branch_command
)


def register_commands(subparsers) -> None:
    """Register Git management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Main git command with subcommands
    git_parser = subparsers.add_parser(
        'git',
        help='Simplified Git operations with safety checks',
        description="""
Git Manager - Simplified Git Operations

This command provides simplified Git operations that wrap complex/tedious workflows
into simple, safe commands with helpful feedback at each step.

All commands include:
• Safety checks with confirmations for destructive operations
• Helpful feedback with colorized output and emoji indicators
• Error handling for common Git issues
• Protection of important branches (main, master, dev)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git wip                     # Quick WIP commit with timestamp
  max git undo-commit             # Safely undo last commit (keep changes staged)
  max git cleanup-branches        # Delete merged branches and prune remotes
  max git sync                    # Fetch, prune, and rebase on upstream
  max git new-branch feature-xyz  # Create branch from latest upstream
  max git safe-force              # Force push with --force-with-lease
        """
    )
    
    # Create subparsers for git subcommands
    git_subparsers = git_parser.add_subparsers(
        title="Git Commands",
        dest="git_command",
        description="Available Git operations",
        metavar="<subcommand>"
    )
    
    # Git WIP command
    wip_parser = git_subparsers.add_parser(
        'wip',
        help='Stage all changes and commit with WIP message and timestamp',
        description="""
Create a Work-In-Progress (WIP) commit with timestamp.

This command:
• Stages all changes (modified, new, and deleted files)
• Creates a commit with message "WIP: YYYY-MM-DD HH:MM ↻"
• Skips if no changes are detected
• Provides feedback on commit creation

Perfect for quickly saving work before switching branches or taking breaks.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git wip                     # Create WIP commit with current timestamp
        """
    )
    wip_parser.set_defaults(func=git_wip_command)
    
    # Git undo-commit command
    undo_parser = git_subparsers.add_parser(
        'undo-commit',
        help='Soft reset last commit and keep changes staged',
        description="""
Safely undo the last commit while keeping changes staged.

This command:
• Shows the commit that will be undone
• Performs a soft reset (git reset --soft HEAD~1)
• Keeps all changes staged and ready for re-commit
• Requires confirmation before proceeding
• Shows commit hash and message being undone

Useful for fixing commit messages or adding forgotten changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git undo-commit             # Undo last commit, keep changes staged
        """
    )
    undo_parser.set_defaults(func=git_undo_commit_command)
    
    # Git redo-commit command  
    redo_parser = git_subparsers.add_parser(
        'redo-commit',
        help='Amend previous commit with staged changes',
        description="""
Amend the previous commit with currently staged changes.

This command:
• Checks for staged changes before proceeding
• Amends the last commit without changing the message
• Preserves original author and date information
• Shows before/after commit information
• Maintains commit history cleanliness

Perfect for adding forgotten files or small fixes to the last commit.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git redo-commit             # Amend last commit with staged changes
        """
    )
    redo_parser.set_defaults(func=git_redo_commit_command)
    
    # Git cleanup-branches command
    cleanup_parser = git_subparsers.add_parser(
        'cleanup-branches',
        help='Delete merged local branches and prune remote-tracking branches',
        description="""
Clean up merged branches and prune remote-tracking branches.

This command:
• Identifies local branches that have been merged into current branch
• Protects important branches (main, master, dev, develop, staging, production)
• Shows list of branches to be deleted before proceeding
• Requires confirmation for destructive operations
• Prunes remote-tracking branches that no longer exist
• Provides detailed feedback on cleanup operations

Keeps your local repository clean and organized.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git cleanup-branches        # Interactive cleanup with confirmation
  max git cleanup-branches --dry-run  # Show what would be deleted
        """
    )
    cleanup_parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    cleanup_parser.set_defaults(func=git_cleanup_branches_command)
    
    # Git track-remote command
    track_parser = git_subparsers.add_parser(
        'track-remote',
        help='Set upstream for current branch and push if needed',
        description="""
Set upstream tracking for the current branch.

This command:
• Sets upstream tracking for the current branch
• Auto-detects remote name (defaults to 'origin')
• Creates remote branch if it doesn't exist
• Pushes local branch to remote when creating new upstream
• Provides confirmation before pushing to new remote branch

Simplifies the process of setting up branch tracking.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git track-remote            # Set upstream using default remote
  max git track-remote upstream   # Set upstream using specific remote
        """
    )
    track_parser.add_argument(
        'remote',
        nargs='?',
        help='Remote name (defaults to auto-detected remote)'
    )
    track_parser.set_defaults(func=git_track_remote_command)
    
    # Git safe-force command
    safe_force_parser = git_subparsers.add_parser(
        'safe-force',
        help='Force push with lease option for safety',
        description="""
Safely force push using --force-with-lease option.

This command:
• Uses --force-with-lease instead of --force for safety
• Shows clear warnings about force pushing
• Requires interactive confirmation
• Displays target branch and remote information
• Prevents overwriting others' changes when possible

Much safer than regular force push as it checks remote state first.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git safe-force              # Force push current branch safely
        """
    )
    safe_force_parser.set_defaults(func=git_safe_force_command)
    
    # Git sync command
    sync_parser = git_subparsers.add_parser(
        'sync',
        help='Fetch all remotes, prune, and rebase current branch on upstream',
        description="""
Synchronize current branch with upstream.

This command:
• Automatically stashes local changes if any exist
• Fetches from all remotes with pruning
• Rebases current branch on its upstream
• Restores stashed changes after sync
• Provides detailed feedback throughout the process
• Handles stash conflicts gracefully

Perfect for staying up-to-date with remote changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git sync                    # Sync current branch with upstream
        """
    )
    sync_parser.set_defaults(func=git_sync_command)
    
    # Git new-branch command
    new_branch_parser = git_subparsers.add_parser(
        'new-branch',
        help='Create new branch from latest upstream and switch to it',
        description="""
Create a new branch from the latest upstream.

This command:
• Fetches latest changes from remote
• Creates new branch from upstream main/master
• Switches to the new branch immediately
• Offers to set upstream tracking
• Validates branch names and prevents conflicts
• Protects against creating branches with reserved names

Streamlines the process of creating feature branches.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max git new-branch feature-auth    # Create feature-auth branch
  max git new-branch bugfix-login    # Create bugfix-login branch
        """
    )
    new_branch_parser.add_argument(
        'name',
        help='Name for the new branch'
    )
    new_branch_parser.set_defaults(func=git_new_branch_command) 