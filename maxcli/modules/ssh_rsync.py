"""
SSH Rsync Module for MaxCLI.

This module provides SSH-based rsync functionality for backup operations including:
- Uploading backups to remote servers via rsync over SSH
- Downloading backups from remote servers via rsync over SSH
- Integration with SSH connection profiles
"""

import argparse
from maxcli.ssh_rsync import handle_rsync_upload_backup, handle_rsync_download_backup


def register_commands(subparsers) -> None:
    """Register SSH rsync commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # SSH rsync command group
    ssh_rsync_parser = subparsers.add_parser(
        'ssh-rsync',
        help='Backup files using rsync over SSH',
        description="""
SSH-based rsync backup functionality for MaxCLI.

This module provides efficient backup operations using rsync over SSH connections.
It integrates with your saved SSH connection profiles to provide easy backup
upload and download capabilities.

Features:
- Uses existing SSH connection profiles
- Efficient incremental backups with rsync
- Secure transfer over SSH
- Preserves file permissions and timestamps
- Progress monitoring for large transfers
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh-rsync upload-backup hetzner    # Upload backup to 'hetzner' server
  max ssh-rsync download-backup backup-server  # Download from 'backup-server'
        """
    )
    
    ssh_rsync_subparsers = ssh_rsync_parser.add_subparsers(
        title="SSH Rsync Commands",
        dest="ssh_rsync_command",
        description="Choose an SSH rsync operation",
        metavar="<command>"
    )
    ssh_rsync_parser.set_defaults(func=handle_rsync_upload_backup)

    # Upload backup command
    upload_parser = ssh_rsync_subparsers.add_parser(
        'upload-backup',
        help='Upload backup files to remote server using rsync',
        description="""
Upload backup files to a remote server using rsync over SSH.

This command uses an existing SSH connection profile to establish the connection
and then transfers files using rsync for efficient incremental backups.

Features:
- Uses saved SSH connection profile for authentication
- Preserves file permissions, ownership, and timestamps  
- Shows transfer progress for large files
- Resumes interrupted transfers
- Only transfers changed files (incremental backup)

The target server must have rsync installed and SSH access configured.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh-rsync upload-backup hetzner    # Upload to 'hetzner' SSH target
  max ssh-rsync upload-backup backup-server --source ~/backups  # Custom source
        """
    )
    upload_parser.add_argument('target', help='SSH target name to upload to')
    upload_parser.add_argument('--source', '-s', help='Source directory to backup (optional)')
    upload_parser.add_argument('--destination', '-d', help='Destination directory on remote server (optional)')
    upload_parser.add_argument('--dry-run', action='store_true', help='Show what would be transferred without actually transferring')
    upload_parser.set_defaults(func=handle_rsync_upload_backup)

    # Download backup command
    download_parser = ssh_rsync_subparsers.add_parser(
        'download-backup',
        help='Download backup files from remote server using rsync',
        description="""
Download backup files from a remote server using rsync over SSH.

This command uses an existing SSH connection profile to establish the connection
and then downloads files using rsync for efficient incremental downloads.

Features:
- Uses saved SSH connection profile for authentication
- Preserves file permissions, ownership, and timestamps
- Shows transfer progress for large files
- Resumes interrupted transfers
- Only downloads changed files (incremental sync)

The remote server must have rsync installed and the backup files accessible.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh-rsync download-backup hetzner  # Download from 'hetzner' SSH target
  max ssh-rsync download-backup backup-server --destination ~/restored  # Custom destination
        """
    )
    download_parser.add_argument('target', help='SSH target name to download from')
    download_parser.add_argument('--source', '-s', help='Source directory on remote server (optional)')
    download_parser.add_argument('--destination', '-d', help='Local destination directory (optional)')
    download_parser.add_argument('--dry-run', action='store_true', help='Show what would be transferred without actually transferring')
    download_parser.set_defaults(func=handle_rsync_download_backup) 