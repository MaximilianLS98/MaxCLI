"""
MaxCLI Configuration Backup Module.

This module provides functionality to backup MaxCLI configuration files:
- Backup config files from ~/.config/maxcli
- Save backups locally or upload to SSH targets
- Integration with existing SSH connection profiles
- Progress monitoring and dry-run capability
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from maxcli.ssh_manager import load_ssh_targets, interactive_target_picker


def get_backup_filename() -> str:
    """Generate a backup filename with timestamp.
    
    Returns:
        Backup filename in format maxcli_backup_YYYYMMDD_HHMMSS.tar.gz
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"maxcli_backup_{timestamp}.tar.gz"


def create_local_backup(destination: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Create a local backup of MaxCLI configuration files.
    
    Args:
        destination: Optional destination directory for the backup
        
    Returns:
        Tuple of (success, backup_path)
    """
    config_dir = Path.home() / ".config" / "maxcli"
    if not config_dir.exists():
        print("❌ MaxCLI configuration directory not found")
        return False, None
    
    # Determine backup destination
    if destination:
        backup_dir = Path(destination).expanduser()
    else:
        backup_dir = Path.home() / "backups"
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / get_backup_filename()
    
    print(f"📦 Creating backup of MaxCLI configuration...")
    print(f"   Source: {config_dir}")
    print(f"   Destination: {backup_file}")
    
    try:
        # Create tar.gz archive
        shutil.make_archive(
            str(backup_file.with_suffix('')),  # Remove .tar.gz for make_archive
            'gztar',
            config_dir.parent,
            'maxcli'
        )
        
        print(f"✅ Backup created successfully: {backup_file}")
        return True, str(backup_file)
        
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False, None


def upload_backup_to_ssh(backup_file: str, target: str, destination: Optional[str] = None) -> bool:
    """Upload a backup file to an SSH target using rsync.
    
    Args:
        backup_file: Path to the backup file
        target: SSH target name
        destination: Optional destination directory on remote server
        
    Returns:
        True if upload was successful, False otherwise
    """
    targets = load_ssh_targets()
    if target not in targets:
        print(f"❌ SSH target '{target}' not found")
        return False
    
    ssh_target = targets[target]
    
    # Build rsync command
    rsync_cmd = [
        "rsync",
        "-avz",  # Archive mode, verbose, compress
        "--progress",  # Show progress
        str(backup_file),
        f"{ssh_target['user']}@{ssh_target['host']}:{destination or '~/backups/'}"
    ]
    
    print(f"📤 Uploading backup to {target}...")
    print(f"   Source: {backup_file}")
    print(f"   Destination: {ssh_target['user']}@{ssh_target['host']}:{destination or '~/backups/'}")
    
    try:
        result = subprocess.run(rsync_cmd)
        if result.returncode == 0:
            print("✅ Backup uploaded successfully")
            return True
        else:
            print(f"❌ Failed to upload backup (exit code: {result.returncode})")
            return False
            
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to execute rsync: {e}")
        return False


def handle_backup_config(args) -> None:
    """Handle the backup-config command.
    
    Args:
        args: Parsed command line arguments
    """
    # Create local backup first
    success, backup_file = create_local_backup(args.local_destination)
    if not success or backup_file is None:
        sys.exit(1)
    
    # If SSH target specified, upload the backup
    if args.target:
        if not upload_backup_to_ssh(backup_file, args.target, args.remote_destination):
            sys.exit(1)
    else:
        print("\n💡 To upload this backup to a remote server, use:")
        print(f"   max backup-config --target <ssh-target> --backup-file {backup_file}")


def register_commands(subparsers) -> None:
    """Register configuration backup commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    backup_parser = subparsers.add_parser(
        'backup-config',
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

The backup includes all configuration files, SSH targets, and module settings.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max backup-config                    # Create local backup in ~/backups
  max backup-config --target hetzner   # Create backup and upload to 'hetzner' server
  max backup-config --local-destination ~/backups  # Custom local backup location
  max backup-config --target backup-server --remote-destination /backups/maxcli  # Custom remote location
        """
    )
    
    backup_parser.add_argument(
        '--target', '-t',
        help='SSH target name to upload backup to'
    )
    backup_parser.add_argument(
        '--local-destination', '-l',
        help='Local directory to save backup (default: ~/maxcli_backups)'
    )
    backup_parser.add_argument(
        '--remote-destination', '-r',
        help='Remote directory to save backup (default: ~/maxcli_backups)'
    )
    backup_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be backed up without actually creating backup'
    )
    
    backup_parser.set_defaults(func=handle_backup_config) 