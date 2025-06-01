"""
Main CLI module with dynamic modular architecture.

This module provides the main entry point for MaxCLI with dynamic module loading
based on user configuration. Modules can be enabled/disabled through the modules
management commands.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .config import init_config
from .modules.module_manager import load_and_register_modules, register_commands as register_module_commands


def get_files_to_remove() -> List[tuple[Path, str]]:
    """Get list of files and directories that MaxCLI creates.
    
    Returns:
        List of tuples containing (path, description) for each item to remove.
    """
    home = Path.home()
    items_to_remove = []
    
    # Configuration directory
    config_dir = home / ".config" / "maxcli"
    if config_dir.exists():
        items_to_remove.append((config_dir, "Configuration directory (~/.config/maxcli/)"))
    
    # Installation files
    maxcli_lib = home / ".local" / "lib" / "python" / "maxcli"
    if maxcli_lib.exists():
        items_to_remove.append((maxcli_lib, "MaxCLI library (~/.local/lib/python/maxcli/)"))
    
    max_executable = home / "bin" / "max"
    if max_executable.exists():
        items_to_remove.append((max_executable, "MaxCLI executable (~/bin/max)"))
    
    # SSH backup files (if they exist)
    ssh_backup_files = [
        home / "ssh_keys_backup.tar.gz",
        home / "ssh_keys_backup.tar.gz.gpg"
    ]
    for backup_file in ssh_backup_files:
        if backup_file.exists():
            items_to_remove.append((backup_file, f"SSH backup file ({backup_file})"))
    
    return items_to_remove


def remove_path_from_shell_config() -> bool:
    """Remove MaxCLI PATH modification from shell configuration files.
    
    Only removes the exact line that MaxCLI adds: 'export PATH="$HOME/bin:$PATH"'
    This is safe and won't affect other PATH configurations.
    
    Returns:
        True if modifications were found and removed, False otherwise.
    """
    shell_configs = [
        Path.home() / ".zshrc",
        Path.home() / ".bashrc",
        Path.home() / ".bash_profile"
    ]
    
    # The exact line that MaxCLI adds - must match exactly
    maxcli_path_line = 'export PATH="$HOME/bin:$PATH"'
    modifications_found = False
    
    for shell_config in shell_configs:
        if not shell_config.exists():
            continue
            
        try:
            # Read the file
            with open(shell_config, 'r') as f:
                lines = f.readlines()
            
            # Find and remove only exact matches
            original_length = len(lines)
            filtered_lines = []
            
            for line in lines:
                stripped_line = line.strip()
                # Only remove if the line is EXACTLY the MaxCLI PATH export
                # This prevents removing:
                # - Lines that contain this as a substring 
                # - Comments that mention this line
                # - More complex PATH exports that include this
                if stripped_line == maxcli_path_line:
                    # Skip this line (remove it)
                    print(f"   🎯 Found and removing exact MaxCLI PATH line: {stripped_line}")
                    continue
                else:
                    # Keep this line
                    filtered_lines.append(line)
            
            # Only write back if we actually removed something
            if len(filtered_lines) < original_length:
                modifications_found = True
                with open(shell_config, 'w') as f:
                    f.writelines(filtered_lines)
                print(f"   ✅ Safely removed MaxCLI PATH modification from {shell_config}")
                print(f"   📊 Removed {original_length - len(filtered_lines)} line(s)")
            
        except (IOError, OSError) as e:
            print(f"   ⚠️  Warning: Could not modify {shell_config}: {e}")
    
    if not modifications_found:
        print("   📝 No MaxCLI PATH modifications found in shell config files")
    
    return modifications_found


def confirm_uninstall(force: bool) -> bool:
    """Get double confirmation from user for uninstall operation.
    
    Args:
        force: If True, skip confirmations.
        
    Returns:
        True if user confirms, False otherwise.
    """
    if force:
        print("🚨 FORCE MODE: Skipping confirmations...")
        return True
    
    print("🚨 WARNING: This will completely remove MaxCLI from your system!")
    print("📋 The following will be permanently deleted:")
    
    # Show what will be removed
    items_to_remove = get_files_to_remove()
    if items_to_remove:
        for _, description in items_to_remove:
            print(f"   • {description}")
    else:
        print("   • No MaxCLI files found to remove")
    
    print("\n💡 This includes:")
    print("   • All your personal configurations")
    print("   • SSH target profiles and connections")
    print("   • API keys and authentication settings")
    print("   • Module configurations and preferences")
    
    # First confirmation
    print("\n" + "="*60)
    response = input("⚡ Are you absolutely sure you want to uninstall MaxCLI? (type 'yes' to confirm): ").strip()
    if response.lower() != 'yes':
        print("❌ Uninstall cancelled.")
        return False
    
    # Second confirmation (double confirmation)
    print("\n🔥 FINAL WARNING: This action is IRREVERSIBLE!")
    print("📝 You will need to re-run the bootstrap script to reinstall MaxCLI.")
    response = input("🗑️  Type 'DELETE EVERYTHING' to proceed with uninstallation: ").strip()
    if response != 'DELETE EVERYTHING':
        print("❌ Uninstall cancelled. Correct phrase not entered.")
        return False
    
    return True


def uninstall_maxcli(args) -> None:
    """Completely uninstall MaxCLI and all its configurations.
    
    Args:
        args: Parsed command line arguments containing force flag.
    """
    print("🗑️  MaxCLI Uninstaller")
    print("=" * 50)
    
    # Get confirmation from user
    if not confirm_uninstall(args.force):
        return
    
    print("\n🚀 Beginning MaxCLI uninstallation...")
    
    # Remove files and directories
    items_to_remove = get_files_to_remove()
    if not items_to_remove:
        print("📂 No MaxCLI files found to remove.")
    else:
        print(f"📂 Removing {len(items_to_remove)} items...")
        
        for path, description in items_to_remove:
            try:
                if path.is_file():
                    path.unlink()
                    print(f"   ✅ Removed file: {description}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"   ✅ Removed directory: {description}")
                else:
                    print(f"   ⚠️  Skipped (not found): {description}")
            except (OSError, IOError) as e:
                print(f"   ❌ Failed to remove {description}: {e}")
    
    # Remove shell configuration modifications
    print("\n🔧 Checking shell configuration files...")
    if remove_path_from_shell_config():
        print("   ✅ Shell PATH modifications removed")
    else:
        print("   📝 No shell modifications found")
    
    # Final message
    print("\n" + "="*50)
    print("✅ MaxCLI uninstallation completed!")
    print("")
    print("📋 Summary:")
    print("   • All MaxCLI files and configurations have been removed")
    print("   • Shell configuration has been cleaned up")
    print("   • Your system has been restored to pre-MaxCLI state")
    print("")
    print("💡 To reinstall MaxCLI in the future:")
    print("   curl -sSL <bootstrap-url> | bash")
    print("")
    print("🔄 You may need to restart your terminal or run 'source ~/.zshrc'")
    print("   to update your PATH environment variable.")


def get_current_version() -> Optional[str]:
    """Get the current MaxCLI version from git if available.
    
    Returns:
        Current git commit hash or tag if available, None otherwise.
    """
    maxcli_install_path = Path.home() / ".local" / "lib" / "python" / "maxcli"
    
    try:
        # First try to get the latest tag
        result = subprocess.run([
            "git", "-C", str(maxcli_install_path), "describe", "--tags", "--exact-match"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return result.stdout.strip()
        
        # If no exact tag match, get the commit hash
        result = subprocess.run([
            "git", "-C", str(maxcli_install_path), "rev-parse", "--short", "HEAD"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return result.stdout.strip()
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return None


def compare_versions(current: str, latest: str) -> bool:
    """Compare two version strings to determine if latest is newer.
    
    Handles both semantic versions (v1.2.3) and commit hashes.
    
    Args:
        current: Current version string.
        latest: Latest version string from GitHub.
        
    Returns:
        True if latest is newer than current, False otherwise.
    """
    # If current is a commit hash (short), any release is considered newer
    if len(current) <= 8 and not current.startswith('v'):
        return True
    
    # Remove 'v' prefix if present for comparison
    current_clean = current.lstrip('v')
    latest_clean = latest.lstrip('v')
    
    # If either isn't a semantic version, fall back to string comparison
    try:
        # Simple semantic version comparison (major.minor.patch)
        current_parts = [int(x) for x in current_clean.split('.')]
        latest_parts = [int(x) for x in latest_clean.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(current_parts), len(latest_parts))
        current_parts.extend([0] * (max_len - len(current_parts)))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        
        return latest_parts > current_parts
        
    except (ValueError, AttributeError):
        # Fall back to string comparison if not semantic versions
        return latest_clean > current_clean


def get_latest_release_version() -> Optional[str]:
    """Get the latest release version from GitHub.
    
    Returns:
        Latest release tag name if available, None otherwise.
    """
    try:
        releases = fetch_github_releases()
        if releases:
            # Get the latest non-prerelease, or latest prerelease if no stable releases
            stable_releases = [r for r in releases if not r.get('prerelease', False)]
            if stable_releases:
                return stable_releases[0].get('tag_name')
            elif releases:
                return releases[0].get('tag_name')
    except Exception:
        pass
    
    return None


def check_for_updates_quietly() -> Tuple[bool, Optional[str]]:
    """Check for available updates using GitHub releases.
    
    Returns:
        Tuple of (updates_available, latest_version)
    """
    try:
        # Get current version
        current_version = get_current_version()
        if not current_version:
            return False, None
        
        # Get latest release from GitHub
        latest_version = get_latest_release_version()
        if not latest_version:
            return False, None
        
        # Compare versions
        has_update = compare_versions(current_version, latest_version)
        return has_update, latest_version if has_update else None
        
    except Exception:
        pass
    
    return False, None


def display_version(args) -> None:
    """Display current MaxCLI version and check for updates.
    
    Args:
        args: Parsed command line arguments (unused but required for consistency).
    """
    print("🚀 MaxCLI - Max's Personal Development CLI")
    print("=" * 50)
    
    # Get current version
    current_version = get_current_version()
    if current_version:
        print(f"📌 Version: {current_version}")
        
        # Check for updates (with a timeout to avoid hanging)
        print("🔍 Checking for updates...", end="", flush=True)
        try:
            updates_available, latest_version = check_for_updates_quietly()
            print(" ✅")
            
            if updates_available and latest_version:
                print(f"🆕 New release available: {latest_version}")
                print("💡 Run 'max update' to get the latest features")
            elif updates_available:
                print("🆕 Updates available!")
                print("💡 Run 'max update' to get the latest features")
            else:
                print("✅ You're running the latest version!")
                
        except Exception:
            print(" ⚠️")
            print("⚠️  Could not check for updates (network issue)")
            
    else:
        print("📌 Version: Unknown (not git-tracked)")
        print("")
        print("💡 To enable version tracking and updates:")
        print("   1. Run 'max update' to initialize git repository")
        print("   2. Then use 'max -v' to check version and updates")
    
    # Repository information
    print(f"\n📂 Installation: ~/.local/lib/python/maxcli/")
    print(f"🔗 Repository: https://github.com/maximilianls98/maxcli")
    print(f"📖 Help: max --help")
    print(f"🔄 Update: max update")


def fetch_github_releases(repo: str = "maximilianls98/maxcli") -> List[dict]:
    """Fetch the latest releases from GitHub API.
    
    Args:
        repo: GitHub repository in format 'owner/repo'.
        
    Returns:
        List of release dictionaries from GitHub API.
    """
    try:
        import urllib.request
        import urllib.error
        
        url = f"https://api.github.com/repos/{repo}/releases"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                content = response.read().decode('utf-8')
                releases = json.loads(content)
                return releases
            else:
                print(f"   ⚠️  GitHub API returned status {response.status}")
    except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
        print(f"   ⚠️  Warning: Could not fetch GitHub releases: {e}")
    
    return []


def display_release_notes(releases: List[dict], current_version: Optional[str] = None) -> None:
    """Display release notes for recent releases.
    
    Args:
        releases: List of release dictionaries from GitHub API.
        current_version: Current installed version to highlight new releases.
    """
    if not releases:
        print("   📝 No release notes available")
        return
    
    print("📋 Recent Release Notes:")
    print("=" * 50)
    
    # Show the latest 3 releases
    for i, release in enumerate(releases[:3]):
        tag = release.get('tag_name', 'Unknown')
        name = release.get('name', tag)
        body = release.get('body', '').strip()
        published_at = release.get('published_at', '')
        is_prerelease = release.get('prerelease', False)
        
        # Format the date
        date_str = ""
        if published_at:
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                date_str = f" ({date_obj.strftime('%Y-%m-%d')})"
            except Exception:
                pass
        
        # Highlight if this is a new version
        version_marker = ""
        if current_version and tag != current_version:
            version_marker = " 🆕"
        elif current_version and tag == current_version:
            version_marker = " ✅"
        
        prerelease_marker = " 🚧" if is_prerelease else ""
        
        print(f"\n🏷️  {name}{version_marker}{prerelease_marker}{date_str}")
        
        if body:
            # Format release notes nicely
            lines = body.split('\n')
            for line in lines:
                if line.strip():
                    print(f"   {line}")
        else:
            print("   No release notes provided")
        
        if i < len(releases[:3]) - 1:
            print("   " + "-" * 45)


def ensure_git_repository() -> bool:
    """Ensure MaxCLI installation is a git repository.
    
    Returns:
        True if git repo is available, False otherwise.
    """
    maxcli_install_path = Path.home() / ".local" / "lib" / "python" / "maxcli"
    
    if not maxcli_install_path.exists():
        print("❌ MaxCLI installation directory not found")
        return False
    
    git_dir = maxcli_install_path / ".git"
    if not git_dir.exists():
        print("📦 Converting MaxCLI installation to git repository...")
        
        try:
            # Initialize git repository
            subprocess.run([
                "git", "-C", str(maxcli_install_path), "init"
            ], check=True, capture_output=True, timeout=10)
            
            # Add remote origin
            subprocess.run([
                "git", "-C", str(maxcli_install_path), "remote", "add", "origin",
                "https://github.com/maximilianls98/maxcli.git"
            ], check=True, capture_output=True, timeout=10)
            
            # Fetch the repository
            subprocess.run([
                "git", "-C", str(maxcli_install_path), "fetch", "origin"
            ], check=True, capture_output=True, timeout=30)
            
            # Reset to match origin/main
            subprocess.run([
                "git", "-C", str(maxcli_install_path), "reset", "--hard", "origin/main"
            ], check=True, capture_output=True, timeout=10)
            
            print("   ✅ Successfully initialized git repository")
            return True
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"   ❌ Failed to initialize git repository: {e}")
            return False
    
    return True


def update_maxcli(args) -> None:
    """Update MaxCLI to the latest version from GitHub.
    
    Args:
        args: Parsed command line arguments containing check_only and show_releases flags.
    """
    print("🔄 MaxCLI Updater")
    print("=" * 50)
    
    maxcli_install_path = Path.home() / ".local" / "lib" / "python" / "maxcli"
    
    # Get current version
    current_version = get_current_version()
    if current_version:
        print(f"📌 Current version: {current_version}")
    else:
        print("📌 Current version: Unknown (not git-tracked)")
    
    # Fetch and display release notes if requested or if checking only
    if args.show_releases or args.check_only:
        print("\n🔍 Fetching release information...")
        releases = fetch_github_releases()
        if releases:
            display_release_notes(releases, current_version)
        else:
            print("   ⚠️  Could not fetch release information")
    
    # If only checking, don't proceed with update
    if args.check_only:
        print(f"\n💡 To update, run: max update")
        return
    
    # Ensure we have a git repository
    if not ensure_git_repository():
        print("\n❌ Cannot proceed without git repository setup")
        print("💡 Consider reinstalling MaxCLI using the bootstrap script")
        return
    
    print("\n🔄 Checking for updates...")
    
    try:
        # Fetch latest changes
        print("   📡 Fetching latest changes from GitHub...")
        subprocess.run([
            "git", "-C", str(maxcli_install_path), "fetch", "origin"
        ], check=True, capture_output=True, timeout=30)
        
        # Check if updates are available using releases
        print("   🔍 Checking for new releases...")
        updates_available, latest_version = check_for_updates_quietly()
        
        if not updates_available:
            print("   ✅ MaxCLI is already up to date!")
            
            # Still show release notes if requested
            if not args.show_releases:
                print("\n💡 To see release notes, run: max update --show-releases")
            return
        else:
            if latest_version:
                print(f"   📦 New release available: {latest_version}")
            else:
                print("   📦 Updates available")
        
        # Pull the latest changes
        print("   ⬇️  Pulling latest changes...")
        if latest_version:
            # Checkout the specific release tag
            print(f"   🏷️  Checking out release {latest_version}...")
            subprocess.run([
                "git", "-C", str(maxcli_install_path), "checkout", latest_version
            ], check=True, capture_output=True, timeout=30)
        else:
            # Fallback to pulling main branch
            subprocess.run([
                "git", "-C", str(maxcli_install_path), "pull", "origin", "main"
            ], check=True, capture_output=True, timeout=30)
        
        # Reinstall dependencies if requirements.txt changed
        print("   🔧 Checking for dependency updates...")
        maxcli_venv = Path.home() / ".venvs" / "maxcli"
        requirements_file = maxcli_install_path.parent.parent.parent / "requirements.txt"
        
        if requirements_file.exists() and maxcli_venv.exists():
            print("   📦 Updating dependencies...")
            subprocess.run([
                str(maxcli_venv / "bin" / "pip"), "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, timeout=60)
            print("   ✅ Dependencies updated")
        else:
            # Fallback: look for requirements.txt in the maxcli repository
            repo_requirements = maxcli_install_path / ".." / "requirements.txt"
            if repo_requirements.exists() and maxcli_venv.exists():
                print("   📦 Updating dependencies from repository...")
                subprocess.run([
                    str(maxcli_venv / "bin" / "pip"), "install", "-r", str(repo_requirements)
                ], check=True, capture_output=True, timeout=60)
                print("   ✅ Dependencies updated")
            else:
                print("   📝 No requirements.txt found or virtual environment missing")
        
        # Get new version
        new_version = get_current_version()
        
        print("\n" + "="*50)
        print("✅ MaxCLI update completed successfully!")
        
        if current_version and new_version and current_version != new_version:
            print(f"📌 Updated from {current_version} to {new_version}")
        elif new_version:
            print(f"📌 Now running version: {new_version}")
        
        # Show recent release notes after update
        if not args.show_releases:
            print("\n🔍 Fetching latest release notes...")
            releases = fetch_github_releases()
            if releases:
                display_release_notes(releases[:1], new_version)  # Show just the latest
        
        print("\n💡 Update complete! All changes are immediately available.")
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\n❌ Update failed: {e}")
        print("💡 Try running the bootstrap script to reinstall:")
        print("   curl -sSL https://raw.githubusercontent.com/maximilianls98/maxcli/main/bootstrap.sh | bash")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog='max', 
        description="Max's Personal CLI - A modular collection of useful development and operations commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Modular CLI System:
MaxCLI uses a modular architecture where functionality is organized into modules.
You can enable/disable modules based on your needs to keep the CLI clean and focused.

Module Management:
  max modules list                # Show all available modules
  max modules enable <module>     # Enable a module
  max modules disable <module>    # Disable a module

Core Commands:
  max init                        # Initialize CLI with your personal configuration
  max update                      # Update MaxCLI to the latest version from GitHub
  max uninstall                   # Completely remove MaxCLI and all configurations
  
Examples of enabled commands (depends on active modules):
  max ssh list-targets            # Show all saved SSH targets (ssh_manager)
  max ssh add-target prod ubuntu 192.168.1.100 (ssh_manager)
  max coolify status              # Check Coolify instance status (coolify_manager)
  max setup minimal               # Basic development environment setup (setup_manager)
  max docker clean --extensive    # Clean up Docker system (docker_manager)
  max kctx my-k8s-context         # Switch Kubernetes context (kubernetes_manager)
  max gcp config switch altekai   # Switch gcloud config (gcp_manager)
  
Use 'max <command> --help' for detailed help on each command.
Use 'max modules list' to see available functionality.
        """
    )
    
    # Add version arguments
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show MaxCLI version information and check for updates'
    )
    
    return parser


def register_core_commands(subparsers) -> None:
    """Register core CLI commands that are always available.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Initialize configuration command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize or update personal configuration',
        description="""
Initialize MaxCLI with your personal configuration settings.

This is a one-time setup (or update) process that collects:
- Git username and email for repository configuration
- Dotfiles repository URL (optional)
- Google Cloud Platform project mappings (optional)
- Coolify instance URL and API key (optional)

The configuration is saved to ~/.config/maxcli/config.json and used by
other commands to personalize their behavior.

After initialization, commands like 'max setup dev-full' will use your
personal git settings and dotfiles repository automatically.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max init                        # First-time setup or update existing config
  max init --force                # Force reconfiguration (skip confirmation)
        """
    )
    init_parser.add_argument('--force', action='store_true', help='Force reconfiguration without confirmation')
    init_parser.set_defaults(func=init_config)

    # Update command
    update_parser = subparsers.add_parser(
        'update',
        help='Update MaxCLI to the latest version from GitHub',
        description="""
🔄 MaxCLI Updater - Keep Your CLI Up to Date

This command updates MaxCLI to the latest release version from GitHub.
It performs the following operations:

🔍 Version Checking:
    • Shows current installed version (git tag or commit hash)
    • Checks for new releases from GitHub repository
    • Only considers formal GitHub releases as updates (not every commit)

📋 Release Notes:
    • Fetches and displays recent release notes from GitHub
    • Highlights new releases with 🆕 markers
    • Shows current release with ✅ markers
    • Indicates pre-releases with 🚧 markers

⚡ Update Process:
    • Automatically initializes git repository if needed
    • Checks out the specific release tag (not main branch)
    • Updates Python dependencies if requirements.txt changed
    • Preserves all personal configurations and module settings

🔧 Safe Operation:
    • Uses git to track changes and ensure clean updates
    • Only updates to stable release versions
    • Maintains virtual environment integrity
    • No data loss - configurations remain intact
    • Immediate availability of new features

The update is performed on the MaxCLI installation at ~/.local/lib/python/maxcli/
and will immediately be available for use without restarting the terminal.

Note: This command only considers formal GitHub releases as updates. Development
commits between releases are not considered "updates" to ensure stability.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max update                      # Update to latest version and show release notes
  max update --check-only         # Check for updates without installing
  max update --show-releases      # Show recent release notes without updating
  max update --check-only --show-releases  # Check updates and show all release notes
        """
    )
    update_parser.add_argument(
        '--check-only', 
        action='store_true', 
        help='Check for updates without installing them'
    )
    update_parser.add_argument(
        '--show-releases', 
        action='store_true', 
        help='Show recent GitHub release notes'
    )
    update_parser.set_defaults(func=update_maxcli)

    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        'uninstall',
        help='Completely remove MaxCLI and all its configurations',
        description="""
⚠️  DANGER: Complete MaxCLI Uninstallation

This command will completely remove MaxCLI from your system, including:

🗂️  Configuration Files:
    • ~/.config/maxcli/ (entire directory)
    • All module configurations and settings
    • SSH target profiles and connections
    • Personal git settings and API keys

📁 Installation Files:
    • ~/.local/lib/python/maxcli/ (MaxCLI library)
    • ~/bin/max (main executable)

🔧 Shell Configuration:
    • PATH modification in ~/.zshrc (if added by MaxCLI)

💾 Backup Files (if they exist):
    • SSH backup files created by ssh_backup module
    • Temporary files in home directory

This operation is IRREVERSIBLE. All your personal configurations, 
SSH targets, API keys, and customizations will be permanently lost.

You will need to re-run the bootstrap script to reinstall MaxCLI.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max uninstall                   # Completely remove MaxCLI (requires double confirmation)
  max uninstall --force           # Skip confirmations (NOT RECOMMENDED)

After uninstall, to reinstall MaxCLI:
  curl -sSL <bootstrap-url> | bash
        """
    )
    uninstall_parser.add_argument(
        '--force', 
        action='store_true', 
        help='Skip all confirmations (DANGEROUS - NOT RECOMMENDED)'
    )
    uninstall_parser.set_defaults(func=uninstall_maxcli)


def main() -> None:
    """Main CLI entry point with dynamic module loading."""
    # Create the main parser
    parser = create_parser()
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="Available Commands", 
        dest="command",
        description="Choose a command to run. Use 'max <command> --help' for detailed help on each command.",
        metavar="<command>"
    )
    
    # Set default behavior when no command is provided
    parser.set_defaults(func=lambda _: parser.print_help())
    
    # Register core commands (always available)
    register_core_commands(subparsers)
    
    # Register module management commands (always available)
    register_module_commands(subparsers)
    
    # Load and register enabled modules dynamically
    load_and_register_modules(subparsers)
    
    # Enable autocomplete if argcomplete is installed
    try:
        import argcomplete  # type: ignore # Optional dependency
        argcomplete.autocomplete(parser)
    except ImportError:
        pass
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle version flag early (before subcommands)
    if hasattr(args, 'version') and args.version:
        display_version(args)
        return
    
    # Execute the appropriate function
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help() 