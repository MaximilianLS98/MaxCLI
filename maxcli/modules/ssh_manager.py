"""
SSH Manager Module for MaxCLI.

This module provides SSH connection profile management functionality including:
- Managing SSH connection profiles 
- Connecting to SSH targets
- Generating and managing SSH keypairs
- Copying public keys to remote hosts
- SSH backup and restore operations
- SSH-based rsync operations
"""

import argparse
from maxcli.ssh_manager import (
    handle_list_targets, handle_add_target, handle_remove_target,
    handle_connect_target, handle_generate_keypair, handle_copy_public_key
)
from maxcli.ssh_backup import handle_export_ssh_keys, handle_import_ssh_keys
from maxcli.ssh_rsync import handle_rsync_upload_backup, handle_rsync_download_backup


def register_commands(subparsers) -> None:
    """Register SSH management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # SSH management command group
    ssh_parser = subparsers.add_parser(
        'ssh',
        help='Manage SSH connections, keys, backups, and transfers',
        description="""
SSH connection, key, backup, and transfer management for MaxCLI.

This module provides comprehensive SSH management including:
- SSH target management (save/list/connect to SSH targets)
- SSH key generation and management
- Public key copying to remote hosts
- SSH key backup and restore with encryption
- File transfers using rsync over SSH
- Secure storage of connection details

All SSH profiles are stored securely in ~/.config/maxcli/ssh_targets.json
with proper file permissions for security.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh targets list            # Show all saved SSH targets
  max ssh targets add prod ubuntu 192.168.1.100 -p 2222 -k ~/.ssh/prod_key
  max ssh connect prod            # Connect to 'prod' SSH target  
  max ssh generate-keypair dev ~/.ssh/dev_key --type ed25519
  max ssh copy-public-key prod    # Copy public key to 'prod' target
  max ssh backup export           # Export SSH keys to encrypted backup
  max ssh backup import           # Import SSH keys from encrypted backup
  max ssh rsync upload-backup prod  # Upload backup to 'prod' target
  max ssh rsync download-backup prod  # Download backup from 'prod' target
        """
    )
    
    ssh_subparsers = ssh_parser.add_subparsers(
        title="SSH Commands",
        dest="ssh_command", 
        description="Choose an SSH management operation",
        metavar="<command>"
    )
    ssh_parser.set_defaults(func=lambda args: ssh_parser.print_help())

    # SSH Targets subcommand group
    targets_parser = ssh_subparsers.add_parser(
        'targets',
        help='Manage SSH connection targets',
        description="""
SSH target management functionality for MaxCLI.

This command group provides target profile management including creating,
listing, and removing SSH connection profiles for easy future connections.

Target profiles store connection details including hostname, username,
port, and private key path. All profiles are stored securely with proper
file permissions for security.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh targets list            # Show all saved SSH targets
  max ssh targets add prod ubuntu 192.168.1.100
  max ssh targets add dev root 10.0.0.5 -p 2222 -k ~/.ssh/dev_key
  max ssh targets remove prod    # Remove the 'prod' target
        """
    )
    
    targets_subparsers = targets_parser.add_subparsers(
        title="Target Management Commands",
        dest="targets_command",
        description="Choose a target management operation",
        metavar="<operation>"
    )
    targets_parser.set_defaults(func=handle_list_targets)

    # List targets command
    list_parser = targets_subparsers.add_parser(
        'list',
        help='List all saved SSH connection targets',
        description="""
Display all saved SSH connection profiles in a formatted table.

Shows target name, username, hostname/IP, port, and private key path
for all configured SSH targets.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max ssh targets list            # Show all SSH targets
        """
    )
    list_parser.set_defaults(func=handle_list_targets)

    # Add target command
    add_parser = targets_subparsers.add_parser(
        'add',
        help='Add a new SSH connection target',
        description="""
Add a new SSH connection profile for easy future connections.

The profile stores the connection details including hostname, username,
port, and private key path. The private key file must exist and be readable.

Target names must be unique. Use remove first if you want to replace
an existing target with the same name.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh targets add prod ubuntu 192.168.1.100
  max ssh targets add dev root 10.0.0.5 -p 2222 -k ~/.ssh/dev_key
  max ssh targets add staging deploy staging.example.com --port 22 --key ~/.ssh/staging
        """
    )
    add_parser.add_argument('name', help='Unique name for this SSH target')
    add_parser.add_argument('user', help='SSH username')
    add_parser.add_argument('host', help='SSH hostname or IP address')
    add_parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22)')
    add_parser.add_argument('-k', '--key', default='~/.ssh/id_rsa', help='Path to private key (default: ~/.ssh/id_rsa)')
    add_parser.set_defaults(func=handle_add_target)

    # Remove target command
    remove_parser = targets_subparsers.add_parser(
        'remove',
        help='Remove an SSH connection target',
        description="""
Remove an SSH connection profile by name.

This only removes the profile from MaxCLI's configuration.
It does not affect the actual SSH keys or remote server.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh targets remove prod      # Remove the 'prod' target
  max ssh targets remove old-server # Remove the 'old-server' target
        """
    )
    remove_parser.add_argument('name', help='Name of the SSH target to remove')
    remove_parser.set_defaults(func=handle_remove_target)

    # Connect command (top-level under ssh)
    connect_parser = ssh_subparsers.add_parser(
        'connect',
        help='Connect to an SSH target',
        description="""
Connect to a saved SSH target using its stored connection details.

If no target name is provided, you'll get an interactive menu to choose
from available targets (requires questionary package for best experience).

The connection uses the stored username, hostname, port, and private key
to establish the SSH session.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh connect prod            # Connect to 'prod' target
  max ssh connect                 # Interactive target selection
  max ssh connect staging         # Connect to 'staging' target
        """
    )
    connect_parser.add_argument('name', nargs='?', help='SSH target name (optional - if not provided, shows interactive menu)')
    connect_parser.set_defaults(func=handle_connect_target)

    # Generate keypair command (top-level under ssh)
    generate_parser = ssh_subparsers.add_parser(
        'generate-keypair',
        help='Generate a new SSH keypair',
        description="""
Generate a new SSH keypair with the specified name and save it to the given path.

Supports multiple key types including RSA, Ed25519, and ECDSA.
Ed25519 is recommended for new keys due to better security and performance.

The generated keypair consists of:
- Private key: saved to the specified path
- Public key: saved to the same path with .pub extension

Both files are created with appropriate permissions for security.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh generate-keypair dev ~/.ssh/dev_key --type ed25519
  max ssh generate-keypair prod ~/.ssh/prod_rsa --type rsa --bits 4096
  max ssh generate-keypair backup ~/.ssh/backup_key
        """
    )
    generate_parser.add_argument('name', help='Name/comment for the key (used in public key)')
    generate_parser.add_argument('key_path', help='Path where the private key will be saved')
    generate_parser.add_argument('--type', default='ed25519', choices=['rsa', 'ed25519', 'ecdsa'], 
                                help='Key type (default: ed25519)')
    generate_parser.add_argument('--bits', type=int, help='Key size in bits (for RSA keys, default: 4096)')
    generate_parser.set_defaults(func=handle_generate_keypair)

    # Copy public key command (top-level under ssh)
    copy_key_parser = ssh_subparsers.add_parser(
        'copy-public-key',
        help='Copy public key to an SSH target using ssh-copy-id',
        description="""
Copy the public key associated with an SSH target to that target's authorized_keys file.

This command uses ssh-copy-id to securely upload your public key to the remote server,
allowing passwordless authentication for future connections. It uses the connection 
details from your saved SSH target profile.

The target must already be configured with 'max ssh targets add', and you must be able
to authenticate to the target (either with password or an existing key).

After successful upload, you'll be prompted whether to disable password authentication
on the remote server for enhanced security.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh copy-public-key prod    # Copy public key to 'prod' target
  max ssh copy-public-key dev     # Copy public key to 'dev' target
        """
    )
    copy_key_parser.add_argument('name', help='SSH target name to copy public key to')
    copy_key_parser.set_defaults(func=handle_copy_public_key)

    # SSH Backup subcommand group
    backup_parser = ssh_subparsers.add_parser(
        'backup',
        help='Backup and restore SSH keys',
        description="""
SSH key backup and restore functionality for MaxCLI.

This module provides secure backup and restore of SSH keys using GPG encryption.
All keys in ~/.ssh/ are backed up to an encrypted archive that can be safely 
stored and transferred.

Features:
- Interactive selection of SSH keys to backup
- GPG encryption with password protection
- Secure backup of both private and public keys
- Preserves file permissions and structure
- Cross-platform restore capability
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh backup export           # Export SSH keys to encrypted backup
  max ssh backup import           # Import SSH keys from encrypted backup
        """
    )
    
    backup_subparsers = backup_parser.add_subparsers(
        title="SSH Backup Commands",
        dest="backup_command",
        description="Choose an SSH backup operation",
        metavar="<operation>"
    )
    backup_parser.set_defaults(func=handle_export_ssh_keys)

    # Export backup command
    export_parser = backup_subparsers.add_parser(
        'export',
        help='Export SSH keys to encrypted backup file',
        description="""
Export selected SSH keys and configuration to a GPG-encrypted backup file.

This command:
1. Scans ~/.ssh/ directory for SSH private keys
2. Provides interactive selection of keys to backup
3. Creates a tar archive of selected keys and their public counterparts
4. Encrypts the archive using GPG with AES-256 encryption
5. Saves the encrypted backup to your home directory

The backup includes:
- Selected private and public key files
- SSH target profiles from MaxCLI configuration
- Proper file permissions preservation

You'll be prompted for a password to encrypt the backup.
Store this password safely - it's required for restore.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh backup export           # Interactive key selection and export
        """
    )
    export_parser.set_defaults(func=handle_export_ssh_keys)

    # Import backup command
    import_parser = backup_subparsers.add_parser(
        'import',
        help='Import SSH keys from encrypted backup file',
        description="""
Import SSH keys and configuration from a GPG-encrypted backup file.

This command:
1. Helps you select from available backup files
2. Prompts for the GPG decryption password
3. Decrypts and validates the backup archive
4. Handles file conflicts with existing SSH keys
5. Restores SSH keys and configuration to ~/.ssh/

SAFETY FEATURES:
- Detects and handles conflicts with existing files
- Asks for confirmation before overwriting
- Provides options to skip or selectively overwrite files
- Validates backup integrity before restore
- Restores proper file permissions (600 for private keys, 644 for public keys)

The restore process preserves the original file structure and permissions.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh backup import           # Interactive backup file selection and import
        """
    )
    import_parser.set_defaults(func=handle_import_ssh_keys)

    # SSH Rsync subcommand group
    rsync_parser = ssh_subparsers.add_parser(
        'rsync',
        help='Transfer backup files using rsync over SSH',
        description="""
SSH-based rsync backup functionality for MaxCLI.

This module provides efficient backup operations using rsync over SSH connections.
It integrates with your saved SSH connection profiles to provide easy backup
upload and download capabilities for SSH key backups.

Features:
- Uses existing SSH connection profiles
- Efficient transfer with rsync
- Secure transfer over SSH
- Preserves file permissions and timestamps
- Progress monitoring for transfers
- Automatic remote directory creation
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh rsync upload-backup hetzner      # Upload backup to 'hetzner' server
  max ssh rsync download-backup backup-server  # Download from 'backup-server'
        """
    )
    
    rsync_subparsers = rsync_parser.add_subparsers(
        title="SSH Rsync Commands",
        dest="rsync_command",
        description="Choose an SSH rsync operation",
        metavar="<operation>"
    )
    rsync_parser.set_defaults(func=lambda args: print("Please specify 'upload-backup' or 'download-backup'"))

    # Upload backup command
    upload_parser = rsync_subparsers.add_parser(
        'upload-backup',
        help='Upload SSH backup to remote server using rsync',
        description="""
Upload SSH backup files to a remote server using rsync over SSH.

This command uses an existing SSH connection profile to establish the connection
and then transfers the encrypted SSH backup file using rsync.

Features:
- Uses saved SSH connection profile for authentication
- Transfers the encrypted SSH backup file created by 'max ssh backup export'
- Creates remote backup directory automatically
- Shows transfer progress
- Secure transfer over SSH

The target server must have rsync installed and SSH access configured.
The backup file must exist in your home directory (created by backup export).
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh rsync upload-backup hetzner    # Upload to 'hetzner' SSH target
  max ssh rsync upload-backup backup-server  # Upload to 'backup-server'
        """
    )
    upload_parser.add_argument('target', help='SSH target name to upload backup to')
    upload_parser.set_defaults(func=handle_rsync_upload_backup)

    # Download backup command
    download_parser = rsync_subparsers.add_parser(
        'download-backup',
        help='Download SSH backup from remote server using rsync',
        description="""
Download SSH backup files from a remote server using rsync over SSH.

This command uses an existing SSH connection profile to establish the connection
and then downloads the encrypted SSH backup file using rsync.

Features:
- Uses saved SSH connection profile for authentication
- Downloads encrypted SSH backup files
- Shows transfer progress
- Secure transfer over SSH
- Overwrites local backup file if it exists

The remote server must have rsync installed and the backup file accessible.
After download, use 'max ssh backup import' to restore the keys.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh rsync download-backup hetzner  # Download from 'hetzner' SSH target
  max ssh rsync download-backup backup-server  # Download from 'backup-server'
        """
    )
    download_parser.add_argument('target', help='SSH target name to download backup from')
    download_parser.set_defaults(func=handle_rsync_download_backup) 