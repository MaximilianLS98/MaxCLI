"""
Main CLI module with dynamic modular architecture.

This module provides the main entry point for MaxCLI with dynamic module loading
based on user configuration. Modules can be enabled/disabled through the modules
management commands.
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import List, Optional

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
    
    # Parse arguments and execute the appropriate function
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help() 