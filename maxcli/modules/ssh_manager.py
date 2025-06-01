"""
SSH Manager Module for MaxCLI.

This module provides SSH connection profile management functionality including:
- Managing SSH connection profiles 
- Connecting to SSH targets
- Generating and managing SSH keypairs
- Copying public keys to remote hosts
"""

import argparse
from maxcli.ssh_manager import (
    handle_list_targets, handle_add_target, handle_remove_target,
    handle_connect_target, handle_generate_keypair, handle_copy_public_key
)


def register_commands(subparsers) -> None:
    """Register SSH management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # SSH management command group
    ssh_parser = subparsers.add_parser(
        'ssh',
        help='Manage SSH connections and keys',
        description="""
SSH connection and key management for MaxCLI.

This module provides comprehensive SSH management including:
- Connection profile management (save/list/connect to SSH targets)
- SSH key generation and management
- Public key copying to remote hosts
- Secure storage of connection details

All SSH profiles are stored securely in ~/.config/maxcli/ssh_targets.json
with proper file permissions for security.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh list-targets            # Show all saved SSH targets
  max ssh add-target prod ubuntu 192.168.1.100 -p 2222 -k ~/.ssh/prod_key
  max ssh connect prod            # Connect to 'prod' SSH target  
  max ssh generate-keypair dev ~/.ssh/dev_key --type ed25519
  max ssh copy-public-key prod    # Copy public key to 'prod' target
        """
    )
    
    ssh_subparsers = ssh_parser.add_subparsers(
        title="SSH Commands",
        dest="ssh_command", 
        description="Choose an SSH management operation",
        metavar="<command>"
    )
    ssh_parser.set_defaults(func=handle_list_targets)

    # List targets command
    list_parser = ssh_subparsers.add_parser(
        'list-targets',
        help='List all saved SSH connection targets',
        description="""
Display all saved SSH connection profiles in a formatted table.

Shows target name, username, hostname/IP, port, and private key path
for all configured SSH targets.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max ssh list-targets            # Show all SSH targets
        """
    )
    list_parser.set_defaults(func=handle_list_targets)

    # Add target command
    add_parser = ssh_subparsers.add_parser(
        'add-target',
        help='Add a new SSH connection target',
        description="""
Add a new SSH connection profile for easy future connections.

The profile stores the connection details including hostname, username,
port, and private key path. The private key file must exist and be readable.

Target names must be unique. Use remove-target first if you want to replace
an existing target with the same name.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh add-target prod ubuntu 192.168.1.100
  max ssh add-target dev root 10.0.0.5 -p 2222 -k ~/.ssh/dev_key
  max ssh add-target staging deploy staging.example.com --port 22 --key ~/.ssh/staging
        """
    )
    add_parser.add_argument('name', help='Unique name for this SSH target')
    add_parser.add_argument('user', help='SSH username')
    add_parser.add_argument('host', help='SSH hostname or IP address')
    add_parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22)')
    add_parser.add_argument('-k', '--key', default='~/.ssh/id_rsa', help='Path to private key (default: ~/.ssh/id_rsa)')
    add_parser.set_defaults(func=handle_add_target)

    # Remove target command
    remove_parser = ssh_subparsers.add_parser(
        'remove-target',
        help='Remove an SSH connection target',
        description="""
Remove an SSH connection profile by name.

This only removes the profile from MaxCLI's configuration.
It does not affect the actual SSH keys or remote server.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max ssh remove-target prod      # Remove the 'prod' target
  max ssh remove-target old-server # Remove the 'old-server' target
        """
    )
    remove_parser.add_argument('name', help='Name of the SSH target to remove')
    remove_parser.set_defaults(func=handle_remove_target)

    # Connect command
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

    # Generate keypair command
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

    # Copy public key command
    copy_key_parser = ssh_subparsers.add_parser(
        'copy-public-key',
        help='Copy public key to an SSH target',
        description="""
Copy the public key associated with an SSH target to that target's authorized_keys file.

This is equivalent to running ssh-copy-id but uses the connection details
from your saved SSH target profile.

The target must already be configured with add-target, and you must be able
to authenticate to the target (either with password or an existing key).
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