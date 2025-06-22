"""Git command implementations for MaxCLI."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

try:
    import git
    from git import Repo, GitError, InvalidGitRepositoryError
except ImportError:
    print("❌ GitPython is required for git commands. Install with: pip install GitPython")
    sys.exit(1)


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# Emoji/Icon constants
ICONS = {
    'success': '✓',
    'warning': '⚠',
    'error': '✗',
    'info': 'ℹ',
    'wip': '↻',
    'branch': '🌿',
    'sync': '🔄',
    'cleanup': '🧹'
}


def colorize(text: str, color: str) -> str:
    """Apply color to text with reset."""
    return f"{color}{text}{Colors.RESET}"


def success(message: str) -> None:
    """Print success message with green color and checkmark."""
    print(colorize(f"[{ICONS['success']}] {message}", Colors.GREEN))


def warning(message: str) -> None:
    """Print warning message with yellow color and warning icon."""
    print(colorize(f"[{ICONS['warning']}] {message}", Colors.YELLOW))


def error(message: str) -> None:
    """Print error message with red color and error icon."""
    print(colorize(f"[{ICONS['error']}] {message}", Colors.RED))


def info(message: str) -> None:
    """Print info message with blue color and info icon."""
    print(colorize(f"[{ICONS['info']}] {message}", Colors.BLUE))


class GitManager:
    """Git repository manager with functional methods."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize GitManager with repository path."""
        try:
            self.repo = Repo(repo_path)
            self.git = self.repo.git
        except InvalidGitRepositoryError:
            error("Not a git repository. Please run from within a git repository.")
            sys.exit(1)
        except Exception as e:
            error(f"Failed to initialize git repository: {e}")
            sys.exit(1)
    
    def has_changes(self) -> bool:
        """Check if repository has any changes (staged or unstaged)."""
        return (
            self.repo.is_dirty() or 
            len(self.repo.untracked_files) > 0 or
            len(list(self.repo.index.diff("HEAD"))) > 0
        )
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "HEAD"  # Detached HEAD state
    
    def get_protected_branches(self) -> List[str]:
        """Get list of protected branch names."""
        return ['main', 'master', 'dev', 'develop', 'staging', 'production']
    
    def get_merged_branches(self) -> List[str]:
        """Get list of local branches that have been merged into current branch."""
        try:
            current_branch = self.get_current_branch()
            protected = self.get_protected_branches()
            
            merged_branches = []
            for branch in self.repo.branches:
                if (branch.name != current_branch and 
                    branch.name not in protected and
                    self.repo.is_ancestor(branch.commit, self.repo.head.commit)):
                    merged_branches.append(branch.name)
            
            return merged_branches
        except Exception as e:
            warning(f"Could not determine merged branches: {e}")
            return []
    
    def get_remote_name(self) -> str:
        """Get primary remote name (defaults to 'origin')."""
        remotes = list(self.repo.remotes)
        if not remotes:
            return 'origin'
        
        # Prefer 'origin' if it exists
        for remote in remotes:
            if remote.name == 'origin':
                return 'origin'
        
        # Otherwise return first remote
        return remotes[0].name
    
    def format_commit_info(self, commit) -> str:
        """Format commit information for display."""
        short_hash = commit.hexsha[:7]
        message = commit.message.strip().split('\n')[0]
        author_date = datetime.fromtimestamp(commit.authored_date)
        relative_date = get_relative_time(author_date)
        
        return f"{short_hash} - {message} ({relative_date})"


def get_relative_time(dt: datetime) -> str:
    """Get relative time string (e.g., '2 minutes ago')."""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def require_git_repo(func):
    """Decorator to ensure command runs in a git repository."""
    def wrapper(args):
        try:
            git_manager = GitManager()
            return func(args, git_manager)
        except SystemExit:
            raise
        except Exception as e:
            error(f"Git operation failed: {e}")
            sys.exit(1)
    return wrapper


def confirm_action(message: str) -> bool:
    """Get confirmation from user for potentially destructive action."""
    try:
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        print()  # New line after interrupt
        info("Operation cancelled by user")
        return False


@require_git_repo
def git_wip_command(args, git_manager: GitManager) -> None:
    """Stage all changes and commit with WIP message and timestamp."""
    if not git_manager.has_changes():
        info("No changes to commit")
        return
    
    try:
        # Stage all changes
        git_manager.repo.git.add(A=True)
        
        # Create WIP commit with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_message = f"WIP: {timestamp} {ICONS['wip']}"
        
        commit = git_manager.repo.index.commit(commit_message)
        
        success(f"Created WIP commit: {git_manager.format_commit_info(commit)}")
        
    except GitError as e:
        error(f"Failed to create WIP commit: {e}")
        sys.exit(1)


@require_git_repo
def git_undo_commit_command(args, git_manager: GitManager) -> None:
    """Soft reset last commit and keep changes staged."""
    try:
        # Get current HEAD commit info before reset
        head_commit = git_manager.repo.head.commit
        commit_info = git_manager.format_commit_info(head_commit)
        
        # Confirm the operation
        if not confirm_action(
            f"This will undo commit: {commit_info}\n"
            f"Changes will be kept staged. Continue?"
        ):
            return
        
        # Soft reset to previous commit
        git_manager.repo.git.reset('--soft', 'HEAD~1')
        
        success(f"Undone commit: {commit_info}")
        info("Changes are now staged and ready for re-commit")
        
    except GitError as e:
        error(f"Failed to undo commit: {e}")
        sys.exit(1)


@require_git_repo
def git_redo_commit_command(args, git_manager: GitManager) -> None:
    """Amend previous commit with staged changes."""
    try:
        # Check if there are staged changes
        if not list(git_manager.repo.index.diff("HEAD")):
            warning("No staged changes to amend")
            return
        
        # Get current commit info
        old_commit = git_manager.repo.head.commit
        old_info = git_manager.format_commit_info(old_commit)
        
        # Amend the commit
        git_manager.repo.git.commit('--amend', '--no-edit')
        
        # Get new commit info
        new_commit = git_manager.repo.head.commit
        new_info = git_manager.format_commit_info(new_commit)
        
        success(f"Amended commit:")
        info(f"  Before: {old_info}")
        info(f"  After:  {new_info}")
        
    except GitError as e:
        error(f"Failed to amend commit: {e}")
        sys.exit(1)


@require_git_repo
def git_cleanup_branches_command(args, git_manager: GitManager) -> None:
    """Delete merged local branches and prune remote-tracking branches."""
    try:
        # Get merged branches
        merged_branches = git_manager.get_merged_branches()
        
        if not merged_branches:
            info("No merged branches to clean up")
        else:
            if args.dry_run:
                info(f"Would delete {len(merged_branches)} merged branches:")
                for branch_name in merged_branches:
                    print(f"  - {branch_name}")
            else:
                # Confirm deletion
                branch_list = '\n'.join(f"  - {b}" for b in merged_branches)
                if not confirm_action(
                    f"This will delete {len(merged_branches)} merged branches:\n{branch_list}\n"
                    f"Continue?"
                ):
                    return
                
                # Delete merged branches
                deleted_count = 0
                for branch_name in merged_branches:
                    try:
                        git_manager.repo.delete_head(branch_name, force=True)
                        success(f"Deleted branch: {branch_name}")
                        deleted_count += 1
                    except GitError as e:
                        warning(f"Could not delete branch {branch_name}: {e}")
                
                success(f"Deleted {deleted_count} merged branches")
        
        # Prune remote-tracking branches
        if args.dry_run:
            info("Would prune remote-tracking branches")
        else:
            try:
                git_manager.repo.git.remote('prune', git_manager.get_remote_name())
                success("Pruned remote-tracking branches")
            except GitError as e:
                warning(f"Could not prune remote branches: {e}")
                
    except Exception as e:
        error(f"Cleanup failed: {e}")
        sys.exit(1)


@require_git_repo
def git_track_remote_command(args, git_manager: GitManager) -> None:
    """Set upstream for current branch and push if needed."""
    try:
        current_branch = git_manager.get_current_branch()
        if current_branch == "HEAD":
            error("Cannot track remote in detached HEAD state")
            return
        
        remote_name = args.remote or git_manager.get_remote_name()
        
        # Check if remote exists
        if remote_name not in [r.name for r in git_manager.repo.remotes]:
            error(f"Remote '{remote_name}' does not exist")
            return
        
        upstream_ref = f"{remote_name}/{current_branch}"
        
        try:
            # Try to set upstream if remote branch exists
            git_manager.repo.git.branch('--set-upstream-to', upstream_ref)
            success(f"Set upstream: {current_branch} -> {upstream_ref}")
        except GitError:
            # Remote branch doesn't exist, push and set upstream
            if confirm_action(f"Remote branch '{upstream_ref}' doesn't exist. Push and set upstream?"):
                git_manager.repo.git.push('--set-upstream', remote_name, current_branch)
                success(f"Pushed and set upstream: {current_branch} -> {upstream_ref}")
                
    except Exception as e:
        error(f"Failed to track remote: {e}")
        sys.exit(1)


@require_git_repo
def git_safe_force_command(args, git_manager: GitManager) -> None:
    """Force push with lease option for safety."""
    try:
        current_branch = git_manager.get_current_branch()
        if current_branch == "HEAD":
            error("Cannot force push in detached HEAD state")
            return
        
        remote_name = git_manager.get_remote_name()
        
        # Show warning and require confirmation
        warning(f"This will force push to {remote_name}/{current_branch}")
        warning("This can overwrite remote changes that others may have pushed")
        
        if not confirm_action("Are you sure you want to force push?"):
            return
        
        # Force push with lease
        git_manager.repo.git.push('--force-with-lease', remote_name, current_branch)
        success(f"Force pushed {current_branch} to {remote_name} (with lease)")
        
    except GitError as e:
        error(f"Force push failed: {e}")
        sys.exit(1)


@require_git_repo
def git_sync_command(args, git_manager: GitManager) -> None:
    """Fetch all remotes, prune, and rebase current branch on upstream."""
    try:
        current_branch = git_manager.get_current_branch()
        if current_branch == "HEAD":
            error("Cannot sync in detached HEAD state")
            return
        
        # Stash changes if any
        stashed = False
        if git_manager.has_changes():
            git_manager.repo.git.stash('push', '-m', f'Auto-stash for sync - {datetime.now()}')
            stashed = True
            info(f"{ICONS['sync']} Stashed local changes")
        
        try:
            # Fetch all remotes with prune
            info(f"{ICONS['sync']} Fetching from all remotes...")
            git_manager.repo.git.fetch('--all', '--prune')
            success("Fetched from all remotes and pruned")
            
            # Try to rebase on upstream
            remote_name = git_manager.get_remote_name()
            upstream_ref = f"{remote_name}/{current_branch}"
            
            try:
                # Check if upstream branch exists
                git_manager.repo.git.rev_parse('--verify', upstream_ref)
                
                info(f"{ICONS['sync']} Rebasing {current_branch} on {upstream_ref}...")
                git_manager.repo.git.rebase(upstream_ref)
                success(f"Rebased {current_branch} on {upstream_ref}")
                
            except GitError as e:
                warning(f"Could not rebase on {upstream_ref}: {e}")
                
        finally:
            # Unstash if we stashed
            if stashed:
                try:
                    git_manager.repo.git.stash('pop')
                    info(f"{ICONS['sync']} Restored stashed changes")
                except GitError as e:
                    warning(f"Could not restore stashed changes: {e}")
                    warning("You may need to manually resolve stash conflicts")
        
        success(f"{ICONS['sync']} Sync completed for {current_branch}")
        
    except Exception as e:
        error(f"Sync failed: {e}")
        sys.exit(1)


@require_git_repo
def git_new_branch_command(args, git_manager: GitManager) -> None:
    """Create new branch from latest upstream and switch to it."""
    try:
        # Validate branch name
        if not args.name or args.name in git_manager.get_protected_branches():
            error(f"Invalid or protected branch name: {args.name}")
            return
        
        # Check if branch already exists
        if args.name in [b.name for b in git_manager.repo.branches]:
            error(f"Branch '{args.name}' already exists locally")
            return
        
        remote_name = git_manager.get_remote_name()
        
        # Determine base branch (main or master)
        base_branch = None
        for branch in ['main', 'master']:
            try:
                git_manager.repo.git.rev_parse('--verify', f"{remote_name}/{branch}")
                base_branch = f"{remote_name}/{branch}"
                break
            except GitError:
                continue
        
        if not base_branch:
            error("Could not find main or master branch on remote")
            return
        
        # Fetch latest
        info(f"{ICONS['branch']} Fetching latest from {remote_name}...")
        git_manager.repo.git.fetch(remote_name)
        
        # Create and checkout new branch
        git_manager.repo.git.checkout('-b', args.name, base_branch)
        success(f"{ICONS['branch']} Created and switched to branch: {args.name}")
        
        # Set upstream
        if confirm_action(f"Set upstream to {remote_name}/{args.name}?"):
            try:
                git_manager.repo.git.push('--set-upstream', remote_name, args.name)
                success(f"Set upstream: {args.name} -> {remote_name}/{args.name}")
            except GitError as e:
                warning(f"Could not set upstream: {e}")
        
    except Exception as e:
        error(f"Failed to create branch: {e}")
        sys.exit(1) 