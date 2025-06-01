"""
SSH Backup Module for MaxCLI.

This module provides SSH key backup and restore functionality including:
- Exporting SSH keys to encrypted backup files
- Importing SSH keys from encrypted backup files
- Secure encryption using password-based encryption
"""

import argparse
from maxcli.ssh_backup import handle_export_ssh_keys, handle_import_ssh_keys


def register_commands(subparsers) -> None:
    """Register SSH backup commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # SSH backup command group
    ssh_backup_parser = subparsers.add_parser(
        'ssh-backup',
        help='Backup and restore SSH keys',
        description="""
SSH key backup and restore functionality for MaxCLI.

This module provides secure backup and restore of SSH keys using password-based
encryption. All keys in ~/.ssh/ are backed up to an encrypted archive that can
be safely stored and transferred.

Features:
- Encrypts SSH keys with password-based encryption
- Backs up all key files (.pub, private keys, known_hosts, config)
- Preserves file permissions and structure
- Cross-platform restore capability
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh-backup export           # Export SSH keys to encrypted backup
  max ssh-backup import           # Import SSH keys from encrypted backup
        """
    )
    
    ssh_backup_subparsers = ssh_backup_parser.add_subparsers(
        title="SSH Backup Commands",
        dest="ssh_backup_command",
        description="Choose an SSH backup operation",
        metavar="<command>"
    )
    ssh_backup_parser.set_defaults(func=handle_export_ssh_keys)

    # Export command
    export_parser = ssh_backup_subparsers.add_parser(
        'export',
        help='Export SSH keys to encrypted backup file',
        description="""
Export all SSH keys and configuration to an encrypted backup file.

This command:
1. Scans ~/.ssh/ directory for all key files and configuration
2. Creates a tar archive of all SSH files
3. Encrypts the archive using password-based encryption (AES-256)
4. Saves the encrypted backup to a timestamped file

The backup includes:
- All private and public key files
- SSH configuration files (config, known_hosts)
- Proper file permissions preservation

You'll be prompted for a password to encrypt the backup.
Store this password safely - it's required for restore.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh-backup export           # Export with default filename
  max ssh-backup export --output backup.enc  # Export to specific file
        """
    )
    export_parser.add_argument('--output', '-o', help='Output backup file path (optional)')
    export_parser.set_defaults(func=handle_export_ssh_keys)

    # Import command
    import_parser = ssh_backup_subparsers.add_parser(
        'import',
        help='Import SSH keys from encrypted backup file',
        description="""
Import SSH keys and configuration from an encrypted backup file.

This command:
1. Prompts for the backup file and decryption password
2. Decrypts and extracts the backup archive
3. Restores SSH keys and configuration to ~/.ssh/
4. Sets proper file permissions for security

SAFETY FEATURES:
- Backs up existing ~/.ssh/ directory before restore
- Asks for confirmation before overwriting existing files
- Validates backup integrity before restore
- Restores proper file permissions (600 for private keys, 644 for public keys)

WARNING: This will overwrite existing SSH configuration.
Make sure to backup your current setup first if needed.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh-backup import           # Import with file selection
  max ssh-backup import --file backup.enc  # Import specific backup file
        """
    )
    import_parser.add_argument('--file', '-f', help='Backup file path to import (optional)')
    import_parser.set_defaults(func=handle_import_ssh_keys) 