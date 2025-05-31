"""SSH key backup and restore functionality for MaxCLI.

This module provides secure backup and restore capabilities for SSH keys and 
SSH target configurations using GPG encryption and interactive selection.
"""

import getpass
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import List, Optional, Tuple, Dict


# Configuration constants
SSH_DIR = Path.home() / ".ssh"
CONFIG_DIR = Path.home() / ".config" / "maxcli"
SSH_TARGETS_FILE = CONFIG_DIR / "ssh_targets.json"
BACKUP_FILENAME = "ssh_keys_backup.tar.gz"
ENCRYPTED_BACKUP_FILENAME = f"{BACKUP_FILENAME}.gpg"


def find_ssh_private_keys() -> List[Path]:
    """Find all SSH private keys in ~/.ssh/ directory.
    
    Returns:
        List of private key file paths. Private keys typically have no extension
        and are not .pub files, config files, or known_hosts.
    """
    if not SSH_DIR.exists():
        return []
    
    private_keys = []
    
    # Common private key patterns and exclusions
    exclude_patterns = {
        '.pub', 'config', 'known_hosts', 'authorized_keys', 
        'known_hosts.old', '.DS_Store'
    }
    
    for file_path in SSH_DIR.iterdir():
        if file_path.is_file():
            # Skip files with .pub extension or common SSH config files
            if (file_path.suffix == '.pub' or 
                file_path.name in exclude_patterns or
                file_path.name.startswith('.')):
                continue
            
            # Check if it's likely a private key by examining first few lines
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline().strip()
                    if (first_line.startswith('-----BEGIN') and 
                        ('PRIVATE KEY' in first_line or 'OPENSSH PRIVATE KEY' in first_line)):
                        private_keys.append(file_path)
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue
    
    return sorted(private_keys)


def get_corresponding_public_key(private_key_path: Path) -> Optional[Path]:
    """Get the corresponding public key file for a private key.
    
    Args:
        private_key_path: Path to the private key file
        
    Returns:
        Path to public key if it exists, None otherwise
    """
    public_key_path = private_key_path.with_suffix('.pub')
    return public_key_path if public_key_path.exists() else None


def interactive_key_selection(available_keys: List[Path]) -> List[Path]:
    """Show interactive selection for SSH keys.
    
    Args:
        available_keys: List of available private key paths
        
    Returns:
        List of selected private key paths
    """
    if not available_keys:
        print("No SSH private keys found in ~/.ssh/")
        return []
    
    try:
        import questionary
        
        # Create choices with key names and corresponding public key info
        choices = []
        for key_path in available_keys:
            pub_key = get_corresponding_public_key(key_path)
            pub_info = " (+ .pub)" if pub_key else " (no .pub)"
            choice_text = f"{key_path.name}{pub_info}"
            choices.append(questionary.Choice(title=choice_text, value=key_path))
        
        selected = questionary.checkbox(
            "Select SSH keys to backup:",
            choices=choices
        ).ask()
        
        return selected if selected else []
        
    except ImportError:
        # Fallback to numbered selection
        print("\nAvailable SSH private keys:")
        for i, key_path in enumerate(available_keys, 1):
            pub_key = get_corresponding_public_key(key_path)
            pub_info = " (+ .pub)" if pub_key else " (no .pub)"
            print(f"  {i}. {key_path.name}{pub_info}")
        
        try:
            selection = input("\nSelect keys (comma-separated numbers, or 'all'): ").strip()
            
            if selection.lower() == 'all':
                return available_keys
            
            selected_keys = []
            for num_str in selection.split(','):
                try:
                    index = int(num_str.strip()) - 1
                    if 0 <= index < len(available_keys):
                        selected_keys.append(available_keys[index])
                except ValueError:
                    continue
            
            return selected_keys
            
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            return []


def create_backup_tarball(selected_keys: List[Path], backup_path: Path) -> bool:
    """Create a tarball with selected SSH keys and config files.
    
    Args:
        selected_keys: List of private key paths to include
        backup_path: Path where to create the backup tarball
        
    Returns:
        True if tarball created successfully, False otherwise
    """
    try:
        with tarfile.open(backup_path, 'w:gz') as tar:
            files_added = 0
            
            # Add selected private keys and their public counterparts
            for private_key in selected_keys:
                # Add private key
                tar.add(private_key, arcname=f"ssh_keys/{private_key.name}")
                files_added += 1
                print(f"  Added: {private_key.name}")
                
                # Add public key if it exists
                public_key = get_corresponding_public_key(private_key)
                if public_key:
                    tar.add(public_key, arcname=f"ssh_keys/{public_key.name}")
                    files_added += 1
                    print(f"  Added: {public_key.name}")
            
            # Add SSH targets configuration if it exists
            if SSH_TARGETS_FILE.exists():
                tar.add(SSH_TARGETS_FILE, arcname="config/ssh_targets.json")
                files_added += 1
                print(f"  Added: ssh_targets.json")
            
            print(f"\n✅ Created backup tarball with {files_added} files")
            return True
            
    except (OSError, tarfile.TarError) as e:
        print(f"Error: Failed to create backup tarball: {e}")
        return False


def encrypt_backup_with_gpg(backup_path: Path, encrypted_path: Path) -> bool:
    """Encrypt the backup tarball using GPG symmetric encryption.
    
    Args:
        backup_path: Path to the unencrypted tarball
        encrypted_path: Path where to save the encrypted file
        
    Returns:
        True if encryption successful, False otherwise
    """
    try:
        # GPG command for symmetric encryption - let GPG handle password prompting
        gpg_cmd = [
            "gpg", "--cipher-algo", "AES256",
            "--compress-algo", "2", "--symmetric",
            "--output", str(encrypted_path),
            str(backup_path)
        ]
        
        print("🔐 Encrypting backup with GPG...")
        print("GPG will prompt you for a password...")
        
        # Let GPG handle password prompting interactively
        result = subprocess.run(gpg_cmd, capture_output=False)
        
        if result.returncode == 0:
            print(f"✅ Backup encrypted successfully: {encrypted_path}")
            return True
        else:
            print(f"Error: GPG encryption failed")
            return False
            
    except FileNotFoundError:
        print("Error: GPG command not found. Make sure GnuPG is installed.")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error: Failed to execute GPG: {e}")
        return False
    except KeyboardInterrupt:
        print("\nEncryption cancelled.")
        return False


def export_ssh_keys() -> bool:
    """Export selected SSH keys and configuration to an encrypted backup.
    
    Returns:
        True if export successful, False otherwise
    """
    print("🔑 SSH Key Export Utility")
    print("=" * 50)
    
    # Find available SSH keys
    available_keys = find_ssh_private_keys()
    if not available_keys:
        print("No SSH private keys found in ~/.ssh/")
        return False
    
    # Interactive key selection
    selected_keys = interactive_key_selection(available_keys)
    if not selected_keys:
        print("No keys selected for backup.")
        return False
    
    print(f"\nSelected {len(selected_keys)} keys for backup:")
    for key in selected_keys:
        pub_key = get_corresponding_public_key(key)
        pub_info = " (+ .pub)" if pub_key else ""
        print(f"  • {key.name}{pub_info}")
    
    # Check for SSH targets config
    if SSH_TARGETS_FILE.exists():
        print(f"  • ssh_targets.json (SSH target profiles)")
    
    # Create backup paths
    backup_path = Path.home() / BACKUP_FILENAME
    encrypted_path = Path.home() / ENCRYPTED_BACKUP_FILENAME
    
    try:
        # Remove existing files if they exist
        if backup_path.exists():
            backup_path.unlink()
        if encrypted_path.exists():
            encrypted_path.unlink()
        
        # Create tarball
        print(f"\n📦 Creating backup tarball...")
        if not create_backup_tarball(selected_keys, backup_path):
            return False
        
        # Encrypt tarball
        encryption_success = encrypt_backup_with_gpg(backup_path, encrypted_path)
        
        # Always clean up unencrypted tarball for security, regardless of encryption result
        if backup_path.exists():
            backup_path.unlink()
            print("🗑️  Removed unencrypted tarball")
        
        if not encryption_success:
            print("❌ Export failed due to encryption error")
            return False
        
        print(f"\n🎉 SSH keys exported successfully!")
        print(f"📁 Encrypted backup: {encrypted_path}")
        print(f"📊 File size: {encrypted_path.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"Error: Export failed: {e}")
        # Clean up on error - always remove unencrypted tarball for security
        for path in [backup_path, encrypted_path]:
            if path.exists():
                try:
                    path.unlink()
                    if path == backup_path:
                        print("🗑️  Removed unencrypted tarball (security cleanup)")
                except OSError:
                    pass
        return False


def select_backup_file() -> Optional[Path]:
    """Interactive selection of backup file to import.
    
    Returns:
        Path to selected backup file or None if cancelled
    """
    home_dir = Path.home()
    
    # Find .tar.gz.gpg files in home directory
    backup_files = list(home_dir.glob("*.tar.gz.gpg"))
    
    if not backup_files:
        # Allow manual file path input
        try:
            file_path = input("Enter path to encrypted backup file (.tar.gz.gpg): ").strip()
            if file_path:
                backup_path = Path(file_path).expanduser()
                if backup_path.exists():
                    return backup_path
                else:
                    print(f"Error: File not found: {backup_path}")
            return None
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            return None
    
    try:
        import questionary
        
        choices = [questionary.Choice(title=f.name, value=f) for f in backup_files]
        choices.append(questionary.Choice(title="Enter custom path...", value=None))
        
        selected = questionary.select(
            "Select backup file to import:",
            choices=choices
        ).ask()
        
        if selected is None:
            # Custom path option
            file_path = questionary.text("Enter path to backup file:").ask()
            if file_path:
                backup_path = Path(file_path).expanduser()
                return backup_path if backup_path.exists() else None
        
        return selected
        
    except ImportError:
        # Fallback to numbered selection
        print("\nAvailable backup files:")
        for i, backup_file in enumerate(backup_files, 1):
            print(f"  {i}. {backup_file.name}")
        print(f"  {len(backup_files) + 1}. Enter custom path")
        
        try:
            choice = input(f"\nSelect backup file (1-{len(backup_files) + 1}): ").strip()
            
            if choice.isdigit():
                index = int(choice) - 1
                if index == len(backup_files):
                    # Custom path option
                    file_path = input("Enter path to backup file: ").strip()
                    if file_path:
                        backup_path = Path(file_path).expanduser()
                        return backup_path if backup_path.exists() else None
                elif 0 <= index < len(backup_files):
                    return backup_files[index]
            
            return None
            
        except (KeyboardInterrupt, EOFError):
            print("\nSelection cancelled.")
            return None


def decrypt_backup_with_gpg(encrypted_path: Path, decrypted_path: Path) -> bool:
    """Decrypt the GPG-encrypted backup file.
    
    Args:
        encrypted_path: Path to encrypted backup file
        decrypted_path: Path where to save decrypted file
        
    Returns:
        True if decryption successful, False otherwise
    """
    try:
        # GPG command for decryption - let GPG handle password prompting
        gpg_cmd = [
            "gpg", "--output", str(decrypted_path),
            "--decrypt", str(encrypted_path)
        ]
        
        print("🔓 Decrypting backup with GPG...")
        print("GPG will prompt you for the decryption password...")
        
        # Let GPG handle password prompting interactively
        result = subprocess.run(gpg_cmd, capture_output=False)
        
        if result.returncode == 0:
            print("✅ Backup decrypted successfully")
            return True
        else:
            print(f"Error: GPG decryption failed. Wrong password or corrupted file.")
            return False
            
    except FileNotFoundError:
        print("Error: GPG command not found. Make sure GnuPG is installed.")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error: Failed to execute GPG: {e}")
        return False
    except KeyboardInterrupt:
        print("\nDecryption cancelled.")
        return False


def validate_backup_contents(backup_path: Path) -> Tuple[bool, List[str]]:
    """Validate the contents of the backup tarball.
    
    Args:
        backup_path: Path to the backup tarball
        
    Returns:
        Tuple of (is_valid, list_of_files)
    """
    try:
        with tarfile.open(backup_path, 'r:gz') as tar:
            files = tar.getnames()
            
            # Check for expected structure
            ssh_keys = [f for f in files if f.startswith('ssh_keys/')]
            config_files = [f for f in files if f.startswith('config/')]
            
            if not ssh_keys:
                print("Warning: No SSH keys found in backup")
            
            return True, files
            
    except tarfile.TarError as e:
        print(f"Error: Invalid backup file: {e}")
        return False, []


def detect_file_conflicts(backup_path: Path) -> Dict[str, Path]:
    """Detect files in backup that would conflict with existing files.
    
    Args:
        backup_path: Path to the backup tarball
        
    Returns:
        Dictionary mapping backup file names to existing file paths
    """
    conflicts = {}
    
    try:
        with tarfile.open(backup_path, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.name.startswith('ssh_keys/'):
                    key_name = member.name.replace('ssh_keys/', '')
                    target_path = SSH_DIR / key_name
                    if target_path.exists():
                        conflicts[key_name] = target_path
                
                elif member.name.startswith('config/'):
                    config_name = member.name.replace('config/', '')
                    if config_name == 'ssh_targets.json':
                        target_path = CONFIG_DIR / config_name
                        if target_path.exists():
                            conflicts[config_name] = target_path
    
    except tarfile.TarError:
        pass
    
    return conflicts


def resolve_file_conflicts(conflicts: Dict[str, Path]) -> Optional[str]:
    """Handle file conflicts with user interaction.
    
    Args:
        conflicts: Dictionary of conflicting files
        
    Returns:
        User's choice: 'overwrite', 'skip', 'individual', or None for cancel
    """
    if not conflicts:
        return 'overwrite'  # No conflicts, proceed normally
    
    print(f"\n⚠️  Found {len(conflicts)} conflicting files:")
    for file_name, existing_path in conflicts.items():
        # Get file size and modification time for comparison
        stat = existing_path.stat()
        size = stat.st_size
        mtime = stat.st_mtime
        from datetime import datetime
        mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  • {file_name} (size: {size:,} bytes, modified: {mod_time})")
    
    print("\nHow would you like to handle these conflicts?")
    print("  1. Overwrite all existing files with backup versions")
    print("  2. Skip all conflicting files (keep existing)")
    print("  3. Ask individually for each conflicting file")
    print("  4. Cancel import")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        choice_map = {
            '1': 'overwrite',
            '2': 'skip',
            '3': 'individual',
            '4': None
        }
        
        return choice_map.get(choice)
        
    except (KeyboardInterrupt, EOFError):
        print("\nImport cancelled.")
        return None


def handle_individual_conflict(file_name: str, existing_path: Path) -> bool:
    """Handle an individual file conflict.
    
    Args:
        file_name: Name of the conflicting file
        existing_path: Path to the existing file
        
    Returns:
        True to overwrite, False to skip
    """
    # Show file info
    stat = existing_path.stat()
    size = stat.st_size
    mtime = stat.st_mtime
    from datetime import datetime
    mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"\n📄 Conflict: {file_name}")
    print(f"   Existing file: {size:,} bytes, modified {mod_time}")
    
    try:
        choice = input("   Overwrite with backup version? [y/N]: ").strip().lower()
        return choice in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        return False


def extract_backup_contents(backup_path: Path) -> bool:
    """Extract backup contents to appropriate locations with conflict handling.
    
    Args:
        backup_path: Path to the backup tarball
        
    Returns:
        True if extraction successful, False otherwise
    """
    try:
        # Ensure directories exist
        SSH_DIR.mkdir(mode=0o700, exist_ok=True)
        CONFIG_DIR.mkdir(parents=True, mode=0o700, exist_ok=True)
        
        # Check for conflicts first
        conflicts = detect_file_conflicts(backup_path)
        conflict_resolution = resolve_file_conflicts(conflicts)
        
        if conflict_resolution is None:
            print("Import cancelled due to conflicts.")
            return False
        
        with tarfile.open(backup_path, 'r:gz') as tar:
            extracted_keys = []
            skipped_files = []
            
            for member in tar.getmembers():
                if member.name.startswith('ssh_keys/'):
                    # Extract SSH key to ~/.ssh/
                    key_name = member.name.replace('ssh_keys/', '')
                    target_path = SSH_DIR / key_name
                    
                    # Handle conflicts based on user choice
                    should_extract = True
                    if key_name in conflicts:
                        if conflict_resolution == 'skip':
                            should_extract = False
                        elif conflict_resolution == 'individual':
                            should_extract = handle_individual_conflict(key_name, target_path)
                        # For 'overwrite', should_extract remains True
                    
                    if should_extract:
                        # Extract the file
                        member.name = key_name  # Remove ssh_keys/ prefix
                        tar.extract(member, SSH_DIR)
                        
                        # Set proper permissions for private keys (no .pub extension)
                        if not key_name.endswith('.pub'):
                            os.chmod(target_path, 0o600)
                            extracted_keys.append(f"🔑 {key_name} (600)")
                        else:
                            os.chmod(target_path, 0o644)
                            extracted_keys.append(f"🔓 {key_name} (644)")
                    else:
                        skipped_files.append(f"⏭️  {key_name} (kept existing)")
                
                elif member.name.startswith('config/'):
                    # Extract config files to ~/.config/maxcli/
                    config_name = member.name.replace('config/', '')
                    
                    if config_name == 'ssh_targets.json':
                        target_path = CONFIG_DIR / config_name
                        
                        # Handle conflicts for config files
                        should_extract = True
                        if config_name in conflicts:
                            if conflict_resolution == 'skip':
                                should_extract = False
                            elif conflict_resolution == 'individual':
                                should_extract = handle_individual_conflict(config_name, target_path)
                        
                        if should_extract:
                            member.name = config_name
                            tar.extract(member, CONFIG_DIR)
                            extracted_keys.append(f"⚙️  ssh_targets.json")
                        else:
                            skipped_files.append(f"⏭️  ssh_targets.json (kept existing)")
            
            # Show results
            if extracted_keys:
                print(f"\n✅ Extracted files:")
                for item in extracted_keys:
                    print(f"  {item}")
            
            if skipped_files:
                print(f"\n⏭️  Skipped files (kept existing):")
                for item in skipped_files:
                    print(f"  {item}")
            
            if not extracted_keys and not skipped_files:
                print("\n⚠️  No files were processed.")
                return False
            
            return True
            
    except (tarfile.TarError, OSError, PermissionError) as e:
        print(f"Error: Failed to extract backup: {e}")
        return False


def import_ssh_keys() -> bool:
    """Import SSH keys and configuration from an encrypted backup.
    
    Returns:
        True if import successful, False otherwise
    """
    print("📥 SSH Key Import Utility")
    print("=" * 50)
    
    # Select backup file
    backup_file = select_backup_file()
    if not backup_file:
        print("No backup file selected.")
        return False
    
    if not backup_file.exists():
        print(f"Error: Backup file not found: {backup_file}")
        return False
    
    print(f"📁 Selected backup: {backup_file.name}")
    
    # Create temporary paths
    decrypted_path = backup_file.with_suffix('')  # Remove .gpg extension
    
    try:
        # Remove existing decrypted file if it exists
        if decrypted_path.exists():
            decrypted_path.unlink()
        
        # Decrypt backup
        if not decrypt_backup_with_gpg(backup_file, decrypted_path):
            return False
        
        # Validate backup contents
        print("🔍 Validating backup contents...")
        is_valid, files = validate_backup_contents(decrypted_path)
        if not is_valid:
            return False
        
        print(f"📋 Backup contains {len(files)} files")
        
        # Confirm extraction
        try:
            confirm = input("\nProceed with extraction? [y/N]: ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Import cancelled.")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\nImport cancelled.")
            return False
        
        # Extract contents
        print("\n📤 Extracting backup contents...")
        if not extract_backup_contents(decrypted_path):
            return False
        
        print(f"\n🎉 SSH keys imported successfully!")
        print(f"🔑 Keys restored to: {SSH_DIR}")
        print(f"⚙️  Config restored to: {CONFIG_DIR}")
        
        return True
        
    except Exception as e:
        print(f"Error: Import failed: {e}")
        return False
        
    finally:
        # Clean up decrypted tarball
        if decrypted_path.exists():
            try:
                decrypted_path.unlink()
                print("🗑️  Removed temporary decrypted file")
            except OSError:
                pass


# CLI handler functions
def handle_export_ssh_keys(args) -> None:
    """CLI handler for ssh-export-keys command."""
    export_ssh_keys()


def handle_import_ssh_keys(args) -> None:
    """CLI handler for ssh-import-keys command."""
    import_ssh_keys() 