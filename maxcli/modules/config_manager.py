from maxcli.backups import create_backup, restore_backup
from maxcli.runtime import CommandError
import shlex
import re
from maxcli.runtime import prompt_input
"""
MaxCLI Configuration Management Module.

This module provides comprehensive configuration management functionality:
- Initialize MaxCLI with personal configuration
- Backup config files from ~/.config/maxcli
- Restore from local or remote backups
- Save backups locally or upload to SSH targets
- Smart merging of local and remote configurations
- Integration with existing SSH connection profiles
- Progress monitoring and dry-run capability
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from maxcli.ssh_manager import load_ssh_targets, interactive_target_picker
from maxcli.config import init_config as _init_config
from maxcli.paths import config_dir

CONFIG_DIR = config_dir()


def get_backup_filename() -> str:
    """Generate a backup filename with timestamp.
    
    Returns:
        Backup filename in format maxcli_backup_YYYYMMDD_HHMMSS.tar.gz
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"maxcli_backup_{timestamp}.tar.gz"


def create_local_backup(destination=None, recipient=None):
    path = create_backup(CONFIG_DIR, destination, recipient)
    print("Backup created: {}".format(path))
    return True, str(path)


def upload_backup_to_ssh(backup_file: str, target: str, destination: Optional[str] = None) -> bool:
    """Upload a backup file to an SSH target using rsync.
    
    Args:
        backup_file: Path to the backup file
        target: SSH target name
        destination: Optional destination directory on remote server
        
    Returns:
        True if upload was successful, False otherwise
    """
    # Verify the backup file exists before attempting upload
    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_file}", file=sys.stderr)
        return False
    
    targets = load_ssh_targets()
    if target not in targets:
        print(f"❌ SSH target '{target}' not found", file=sys.stderr)
        return False
    
    ssh_target = targets[target]
    
    # Build rsync command with proper SSH options
    ssh_options = shlex.join(["ssh", "-i", ssh_target["key"], "-p", str(ssh_target.get("port", 22))])
    rsync_cmd = [
        "rsync",
        "-avz",  # Archive mode, verbose, compress
        "--progress",  # Show progress
        "-e", ssh_options,  # Use custom SSH options
        str(backup_path),  # Use resolved path
        f"{ssh_target['user']}@{ssh_target['host']}:{destination or '~/backups/'}"
    ]
    
    print(f"📤 Uploading backup to {target}...")
    print(f"   Source: {backup_path} ({backup_path.stat().st_size} bytes)")
    print(f"   Destination: {ssh_target['user']}@{ssh_target['host']}:{destination or '~/backups/'}")
    
    try:
        result = subprocess.run(rsync_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Backup uploaded successfully")
            return True
        else:
            print(f"❌ Failed to upload backup (exit code: {result.returncode})", file=sys.stderr)
            if result.stderr:
                print(f"   Error details: {result.stderr.strip()}")
            return False
            
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to execute rsync: {e}", file=sys.stderr)
        return False


def download_backup_from_ssh(target: str, backup_file: str, destination: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Download a backup file from an SSH target using rsync.
    
    Args:
        target: SSH target name
        backup_file: Name of the backup file on remote server
        destination: Optional local destination directory
        
    Returns:
        Tuple of (success, local_path)
    """
    targets = load_ssh_targets()
    if target not in targets:
        print(f"❌ SSH target '{target}' not found", file=sys.stderr)
        return False, None
    
    ssh_target = targets[target]
    
    # Determine local destination
    if destination:
        local_dir = Path(destination).expanduser()
    else:
        local_dir = Path.home() / "backups"
    
    if not re.fullmatch(r'maxcli_backup_[A-Za-z0-9_.-]+\.tar\.gz(?:\.gpg)?', backup_file):
        raise CommandError('Invalid remote backup filename')
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / backup_file
    
    # Build rsync command
    rsync_cmd = [
        "rsync",
        "-avz",  # Archive mode, verbose, compress
        "--progress",  # Show progress
        "-e", shlex.join(["ssh", "-i", ssh_target["key"], "-p", str(ssh_target.get("port", 22))]),
        f"{ssh_target['user']}@{ssh_target['host']}:~/backups/{backup_file}",
        str(local_file)
    ]
    
    print(f"📥 Downloading backup from {target}...")
    print(f"   Source: {ssh_target['user']}@{ssh_target['host']}:~/backups/{backup_file}")
    print(f"   Destination: {local_file}")
    
    try:
        result = subprocess.run(rsync_cmd)
        if result.returncode == 0:
            print("✅ Backup downloaded successfully")
            return True, str(local_file)
        else:
            print(f"❌ Failed to download backup (exit code: {result.returncode})", file=sys.stderr)
            return False, None
            
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to execute rsync: {e}", file=sys.stderr)
        return False, None


def list_remote_backups(target: str) -> List[str]:
    """List available backups on a remote SSH target.
    
    Args:
        target: SSH target name
        
    Returns:
        List of backup filenames
    """
    targets = load_ssh_targets()
    if target not in targets:
        print(f"❌ SSH target '{target}' not found", file=sys.stderr)
        return []
    
    ssh_target = targets[target]
    
    # Build SSH command to list backups
    ssh_cmd = [
        "ssh", "-i", ssh_target["key"], "-p", str(ssh_target.get("port", 22)),
        f"{ssh_target['user']}@{ssh_target['host']}",
        "ls -1 ~/backups/maxcli_backup_*.tar.gz* 2>/dev/null || echo ''"
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            backups = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return [Path(b).name for b in backups]
        else:
            print(f"❌ Failed to list remote backups (exit code: {result.returncode})", file=sys.stderr)
            return []
            
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to execute SSH command: {e}", file=sys.stderr)
        return []


def restore_config(backup_file: str, merge: bool = False) -> bool:
    restore_backup(backup_file, CONFIG_DIR, merge)
    return True


def handle_config_init(args) -> None:
    """Handle the config init command."""
    _init_config(args)


def handle_config_backup(args):
    if args.encrypt and not args.recipient:
        raise CommandError('--encrypt requires --recipient GPG_KEY_ID')
    if args.recipient and not args.encrypt:
        raise CommandError('--recipient requires --encrypt')
    if args.dry_run:
        print('Back up supported JSON configuration from {} ({})'.format(
            CONFIG_DIR, 'encrypted, including credentials' if args.encrypt else 'recognized secret fields excluded'))
        return
    success, backup_file = create_local_backup(args.local_destination, args.recipient)
    if args.target:
        return upload_backup_to_ssh(backup_file, args.target, args.remote_destination)
    return success


def handle_config_restore(args):
    local_file = args.backup_file
    if args.target:
        if not local_file:
            backups = list_remote_backups(args.target)
            if not backups:
                raise CommandError('No remote backups found')
            for i, name in enumerate(backups, 1):
                print('{}: {}'.format(i, name))
            choice = int(prompt_input('Select backup number: '))
            if not 1 <= choice <= len(backups):
                raise CommandError('Invalid backup selection')
            local_file = backups[choice - 1]
        if args.dry_run:
            print('Would download {} from {} and validate before restore'.format(local_file, args.target))
            return
        success, local_file = download_backup_from_ssh(args.target, local_file, args.local_destination)
        if not success:
            return False
    if not local_file:
        raise CommandError('--backup-file is required')
    if not args.dry_run and not args.yes:
        if prompt_input('Restore configuration, preserving a recovery copy? [y/N]: ').lower() not in ('y', 'yes'):
            raise CommandError('Restore cancelled')
    restore_backup(local_file, CONFIG_DIR, merge=args.merge, dry_run=args.dry_run)
    return True


def register_commands(subparsers) -> None:
    """Register configuration management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Main config command
    config_parser = subparsers.add_parser(
        'config',
        help='Configuration management for MaxCLI',
        description="""
Comprehensive configuration management for MaxCLI.

This command provides tools to initialize, backup, and restore your MaxCLI configuration.
All your personal settings, SSH targets, module configurations, and API keys are
managed through these subcommands.

Configuration files are stored in ~/.config/maxcli/ and include:
- Personal git settings and API keys
- SSH target profiles and connections  
- Module enable/disable settings
- Dotfiles repository configuration
- GCP project mappings

The backup and restore functionality allows you to sync your configuration across
multiple machines or create snapshots before making changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max config init                      # Initialize or update personal configuration
  max config backup                    # Create local backup in ~/backups
  max config backup --target hetzner   # Create backup and upload to 'hetzner' server
  max config restore --target hetzner  # List and restore from remote backup
  max config restore --backup-file ~/backups/maxcli_backup_20240321.tar.gz  # Restore from local backup
        """
    )
    
    config_subparsers = config_parser.add_subparsers(
        title="Configuration Commands",
        dest="config_command",
        description="Choose a configuration operation",
        metavar="<command>"
    )
    config_parser.set_defaults(func=lambda _: config_parser.print_help())

    # Init subcommand
    init_parser = config_subparsers.add_parser(
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
  max config init                      # First-time setup or update existing config
  max config init --force              # Force reconfiguration (skip confirmation)
        """
    )
    init_parser.add_argument('--force', action='store_true', help='Force reconfiguration without confirmation')
    init_parser.set_defaults(func=handle_config_init)

    # Backup subcommand
    backup_parser = config_subparsers.add_parser(
        'backup',
        help='Backup MaxCLI configuration files',
        description="""
Backup MaxCLI configuration files from ~/.config/maxcli.

This command creates a backup of your MaxCLI configuration files and can optionally
upload it to a remote server using an existing SSH target.

Features:
- Creates timestamped backup archives
- Option to save locally or upload to SSH target
- Uses existing SSH connection profiles
- Preserves file permissions and timestamps
- Progress monitoring for uploads

Only supported JSON configuration files are included. Recognized secret fields are excluded unless --encrypt is used.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max config backup                    # Create local backup in ~/backups
  max config backup --target hetzner   # Create backup and upload to 'hetzner' server
  max config backup --local-destination ~/backups  # Custom local backup location
  max config backup --target backup-server --remote-destination /backups/maxcli  # Custom remote location
        """
    )
    
    backup_parser.add_argument(
        '--target', '-t',
        help='SSH target name to upload backup to'
    )
    backup_parser.add_argument(
        '--local-destination', '-l',
        help='Local directory to save backup (default: ~/backups)'
    )
    backup_parser.add_argument(
        '--remote-destination', '-r',
        help='Remote directory to save backup (default: ~/backups)'
    )
    backup_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be backed up without actually creating backup'
    )
    
    backup_parser.add_argument('--encrypt', action='store_true', help='Encrypt backup including credentials with GPG')
    backup_parser.add_argument('--recipient', help='GPG recipient key ID')
    backup_parser.set_defaults(func=handle_config_backup)

    # Restore subcommand
    restore_parser = config_subparsers.add_parser(
        'restore',
        help='Restore MaxCLI configuration from backup',
        description="""
Restore MaxCLI configuration from a local or remote backup.

This command can restore your MaxCLI configuration from:
- A local backup file
- A backup stored on a remote SSH target

Features:
- Restore from local or remote backups
- Interactive backup selection for remote backups
- Option to keep, replace, or merge with existing configuration
- Automatic backup of existing configuration before restore
- Smart merging of module configurations

The restore process is safe and will create a backup of your existing
configuration before making any changes.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max config restore --backup-file ~/backups/maxcli_backup_20240321.tar.gz  # Restore from local backup
  max config restore --target hetzner  # List and restore from remote backup
  max config restore --target backup-server --local-destination ~/restored  # Custom restore location
        """
    )
    
    restore_parser.add_argument(
        '--target', '-t',
        help='SSH target name to restore from'
    )
    restore_parser.add_argument(
        '--backup-file', '-b',
        help='Local backup file to restore from (required if not using --target)'
    )
    restore_parser.add_argument(
        '--local-destination', '-l',
        help='Local directory to save downloaded backup (default: ~/backups)'
    )
    
    restore_parser.add_argument('--dry-run', action='store_true')
    restore_parser.add_argument('--yes', action='store_true', help='Approve restore without prompting')
    restore_parser.add_argument('--merge', action='store_true', help='Merge incoming values into local configuration')
    restore_parser.set_defaults(func=handle_config_restore)
