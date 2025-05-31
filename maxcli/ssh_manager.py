"""SSH connection profile manager for MaxCLI.

This module provides functionality to manage SSH connection profiles,
including storing profiles in JSON, connecting to targets, and managing SSH keys.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Configuration constants
CONFIG_DIR = Path.home() / ".config" / "maxcli"
SSH_TARGETS_FILE = CONFIG_DIR / "ssh_targets.json"


def ensure_config_directory() -> None:
    """Ensure the maxcli config directory exists with proper permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, 0o700)


def load_ssh_targets() -> Dict[str, Dict]:
    """Load SSH targets from the JSON configuration file.
    
    Returns:
        Dictionary of SSH targets with name as key and profile data as value.
        Returns empty dict if file doesn't exist or is invalid.
    """
    if not SSH_TARGETS_FILE.exists():
        return {}
    
    try:
        with open(SSH_TARGETS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load SSH targets file: {e}")
        return {}


def save_ssh_targets(targets: Dict[str, Dict]) -> bool:
    """Save SSH targets to the JSON configuration file with proper permissions.
    
    Args:
        targets: Dictionary of SSH targets to save.
        
    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        ensure_config_directory()
        
        with open(SSH_TARGETS_FILE, 'w') as f:
            json.dump(targets, f, indent=2)
        
        # Set file permissions to 600 (read/write for owner only)
        os.chmod(SSH_TARGETS_FILE, 0o600)
        return True
        
    except (IOError, OSError) as e:
        print(f"Error: Could not save SSH targets file: {e}")
        return False


def validate_ssh_target(user: str, host: str, port: int, key: str) -> Tuple[bool, Optional[str]]:
    """Validate SSH target parameters.
    
    Args:
        user: SSH username
        host: SSH hostname or IP
        port: SSH port number
        key: Path to private key file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not user.strip():
        return False, "Username cannot be empty"
    
    if not host.strip():
        return False, "Host cannot be empty"
    
    if not (1 <= port <= 65535):
        return False, "Port must be between 1 and 65535"
    
    key_path = Path(key).expanduser()
    if not key_path.exists():
        return False, f"Private key file does not exist: {key_path}"
    
    if not key_path.is_file():
        return False, f"Private key path is not a file: {key_path}"
    
    return True, None


def format_targets_table(targets: Dict[str, Dict]) -> str:
    """Format SSH targets as a readable table.
    
    Args:
        targets: Dictionary of SSH targets
        
    Returns:
        Formatted string table
    """
    if not targets:
        return "No SSH targets configured."
    
    # Calculate column widths
    name_width = max(len("Name"), max(len(name) for name in targets.keys()))
    user_width = max(len("User"), max(len(target["user"]) for target in targets.values()))
    host_width = max(len("Host"), max(len(target["host"]) for target in targets.values()))
    port_width = max(len("Port"), max(len(str(target.get("port", 22))) for target in targets.values()))
    
    # Create header
    header = f"{'Name':<{name_width}} {'User':<{user_width}} {'Host':<{host_width}} {'Port':<{port_width}} Key"
    separator = "-" * len(header)
    
    # Create rows
    rows = []
    for name, target in sorted(targets.items()):
        port = target.get("port", 22)
        key = target["key"]
        row = f"{name:<{name_width}} {target['user']:<{user_width}} {target['host']:<{host_width}} {port:<{port_width}} {key}"
        rows.append(row)
    
    return f"{header}\n{separator}\n" + "\n".join(rows)


def list_targets() -> None:
    """List all saved SSH targets in a formatted table."""
    targets = load_ssh_targets()
    print(format_targets_table(targets))


def add_target(name: str, user: str, host: str, port: int = 22, key: str = "~/.ssh/id_rsa") -> bool:
    """Add a new SSH target profile.
    
    Args:
        name: Unique identifier for the target
        user: SSH username
        host: SSH hostname or IP address
        port: SSH port (default: 22)
        key: Path to private key file (default: ~/.ssh/id_rsa)
        
    Returns:
        True if target was added successfully, False otherwise
    """
    # Validate inputs
    is_valid, error_msg = validate_ssh_target(user, host, port, key)
    if not is_valid:
        print(f"Error: {error_msg}")
        return False
    
    # Load existing targets
    targets = load_ssh_targets()
    
    # Check if target already exists
    if name in targets:
        print(f"Error: SSH target '{name}' already exists. Use remove-target first to replace it.")
        return False
    
    # Add new target
    targets[name] = {
        "user": user.strip(),
        "host": host.strip(),
        "port": port,
        "key": str(Path(key).expanduser())
    }
    
    # Save targets
    if save_ssh_targets(targets):
        print(f"✅ SSH target '{name}' added successfully.")
        return True
    else:
        return False


def remove_target(name: str) -> bool:
    """Remove an SSH target by name.
    
    Args:
        name: Name of the target to remove
        
    Returns:
        True if target was removed successfully, False otherwise
    """
    targets = load_ssh_targets()
    
    if name not in targets:
        print(f"Error: SSH target '{name}' not found.")
        return False
    
    del targets[name]
    
    if save_ssh_targets(targets):
        print(f"✅ SSH target '{name}' removed successfully.")
        return True
    else:
        return False


def connect_target(name: Optional[str] = None) -> bool:
    """Connect to an SSH target using the stored profile.
    
    Args:
        name: Name of the target to connect to. If None, shows interactive picker.
        
    Returns:
        True if connection was initiated successfully, False otherwise
    """
    targets = load_ssh_targets()
    
    if not targets:
        print("No SSH targets configured. Use 'add-target' to create one first.")
        return False
    
    # Interactive target selection if name not provided
    if name is None:
        name = interactive_target_picker(list(targets.keys()))
        if name is None:
            return False
    
    # Validate target exists
    if name not in targets:
        print(f"Error: SSH target '{name}' not found.")
        print("Available targets:")
        list_targets()
        return False
    
    target = targets[name]
    
    # Build SSH command
    ssh_cmd = [
        "ssh",
        "-i", target["key"],
        "-p", str(target["port"]),
        f"{target['user']}@{target['host']}"
    ]
    
    print(f"🔗 Connecting to {name} ({target['user']}@{target['host']}:{target['port']})...")
    
    try:
        # Execute SSH command (replaces current process)
        os.execvp("ssh", ssh_cmd)
        return True
    except OSError as e:
        print(f"Error: Failed to execute SSH command: {e}")
        print("Make sure SSH client is installed and in your PATH.")
        return False


def interactive_target_picker(target_names: List[str]) -> Optional[str]:
    """Show an interactive target picker.
    
    Args:
        target_names: List of available target names
        
    Returns:
        Selected target name or None if cancelled
    """
    try:
        # Try to use questionary for better UX
        import questionary
        return questionary.select(
            "Select SSH target:",
            choices=target_names
        ).ask()
    except ImportError:
        # Fallback to simple numbered selection
        print("\nAvailable SSH targets:")
        for i, name in enumerate(target_names, 1):
            print(f"  {i}. {name}")
        
        try:
            choice = input("\nSelect target (number or name): ").strip()
            
            # Try as number first
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(target_names):
                    return target_names[index]
            
            # Try as name
            if choice in target_names:
                return choice
            
            print("Invalid selection.")
            return None
            
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return None


def generate_keypair(name: str, key_path: str, key_type: str = "ed25519") -> bool:
    """Generate a new SSH keypair.
    
    Args:
        name: Identifier for the keypair (used in comment)
        key_path: Path where to save the private key
        key_type: Type of key to generate (default: ed25519)
        
    Returns:
        True if keypair was generated successfully, False otherwise
    """
    key_path = Path(key_path).expanduser()
    
    # Ensure parent directory exists
    key_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if key already exists
    if key_path.exists():
        try:
            overwrite = input(f"Key file {key_path} already exists. Overwrite? [y/N]: ").strip().lower()
            if overwrite not in ['y', 'yes']:
                print("Key generation cancelled.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\nKey generation cancelled.")
            return False
    
    # Build ssh-keygen command
    keygen_cmd = [
        "ssh-keygen",
        "-t", key_type,
        "-f", str(key_path),
        "-C", f"{name}@maxcli-generated",
        "-N", ""  # No passphrase
    ]
    
    print(f"🔑 Generating {key_type} keypair at {key_path}...")
    
    try:
        result = subprocess.run(keygen_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SSH keypair generated successfully:")
            print(f"   Private key: {key_path}")
            print(f"   Public key:  {key_path}.pub")
            
            # Set proper permissions
            os.chmod(key_path, 0o600)
            os.chmod(f"{key_path}.pub", 0o644)
            
            return True
        else:
            print(f"Error: Failed to generate SSH keypair:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("Error: ssh-keygen command not found. Make sure OpenSSH is installed.")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error: Failed to execute ssh-keygen: {e}")
        return False


def copy_public_key(name: str) -> bool:
    """Copy public key to the server using ssh-copy-id.
    
    Args:
        name: Name of the SSH target
        
    Returns:
        True if public key was copied successfully, False otherwise
    """
    targets = load_ssh_targets()
    
    if name not in targets:
        print(f"Error: SSH target '{name}' not found.")
        return False
    
    target = targets[name]
    key_path = Path(target["key"]).expanduser()
    public_key_path = Path(f"{key_path}.pub")
    
    # Verify public key exists
    if not public_key_path.exists():
        print(f"Error: Public key file does not exist: {public_key_path}")
        print(f"Generate a keypair first using: generate-keypair {name} {key_path}")
        return False
    
    # Build ssh-copy-id command
    copy_cmd = [
        "ssh-copy-id",
        "-i", str(public_key_path),
        "-p", str(target["port"]),
        f"{target['user']}@{target['host']}"
    ]
    
    print(f"🔑 Copying public key to {name} ({target['user']}@{target['host']})...")
    
    try:
        result = subprocess.run(copy_cmd)
        
        if result.returncode == 0:
            print(f"✅ Public key copied successfully to {name}")
            return True
        else:
            print(f"Error: Failed to copy public key (exit code: {result.returncode})")
            return False
            
    except FileNotFoundError:
        print("Error: ssh-copy-id command not found. Make sure OpenSSH is installed.")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error: Failed to execute ssh-copy-id: {e}")
        return False


# Convenience functions for CLI integration
def handle_list_targets(args) -> None:
    """CLI handler for list-targets command."""
    list_targets()


def handle_add_target(args) -> None:
    """CLI handler for add-target command."""
    port = getattr(args, 'port', 22) or 22
    key = getattr(args, 'key', '~/.ssh/id_rsa') or '~/.ssh/id_rsa'
    add_target(args.name, args.user, args.host, port, key)


def handle_remove_target(args) -> None:
    """CLI handler for remove-target command."""
    remove_target(args.name)


def handle_connect_target(args) -> None:
    """CLI handler for connect command."""
    name = getattr(args, 'name', None)
    connect_target(name)


def handle_generate_keypair(args) -> None:
    """CLI handler for generate-keypair command."""
    key_type = getattr(args, 'type', 'ed25519') or 'ed25519'
    generate_keypair(args.name, args.key_path, key_type)


def handle_copy_public_key(args) -> None:
    """CLI handler for copy-public-key command."""
    copy_public_key(args.name) 