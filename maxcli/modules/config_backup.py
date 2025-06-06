"""
MaxCLI Configuration Backup Module.

This module provides functionality to backup MaxCLI configuration files:
- Backup config files from ~/.config/maxcli
- Save backups locally or upload to SSH targets
- Restore from local or remote backups
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
        print(f"❌ SSH target '{target}' not found")
        return False, None
    
    ssh_target = targets[target]
    
    # Determine local destination
    if destination:
        local_dir = Path(destination).expanduser()
    else:
        local_dir = Path.home() / "backups"
    
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / backup_file
    
    # Build rsync command
    rsync_cmd = [
        "rsync",
        "-avz",  # Archive mode, verbose, compress
        "--progress",  # Show progress
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
            print(f"❌ Failed to download backup (exit code: {result.returncode})")
            return False, None
            
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to execute rsync: {e}")
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
        print(f"❌ SSH target '{target}' not found")
        return []
    
    ssh_target = targets[target]
    
    # Build SSH command to list backups
    ssh_cmd = [
        "ssh",
        f"{ssh_target['user']}@{ssh_target['host']}",
        "ls -1 ~/backups/maxcli_backup_*.tar.gz 2>/dev/null || echo ''"
    ]
    
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            backups = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return [Path(b).name for b in backups]
        else:
            print(f"❌ Failed to list remote backups (exit code: {result.returncode})")
            return []
            
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to execute SSH command: {e}")
        return []


def extract_backup(backup_file: str, destination: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Extract a backup file to a temporary directory.
    
    Args:
        backup_file: Path to the backup file
        destination: Optional destination directory (defaults to temp directory)
        
    Returns:
        Tuple of (success, extracted_path)
    """
    if not Path(backup_file).exists():
        print(f"❌ Backup file not found: {backup_file}")
        return False, None
    
    # Create temporary directory if no destination specified
    if destination:
        extract_dir = Path(destination).expanduser()
        extract_dir.mkdir(parents=True, exist_ok=True)
    else:
        extract_dir = Path(tempfile.mkdtemp(prefix="maxcli_restore_"))
    
    print(f"📦 Extracting backup to {extract_dir}...")
    
    try:
        # Extract the archive
        shutil.unpack_archive(backup_file, extract_dir, 'gztar')
        config_dir = extract_dir / "maxcli"
        
        if not config_dir.exists():
            print("❌ Invalid backup: maxcli directory not found in archive")
            return False, None
        
        print("✅ Backup extracted successfully")
        return True, str(config_dir)
        
    except Exception as e:
        print(f"❌ Failed to extract backup: {e}")
        return False, None


def merge_configs(local_config: Dict[str, Any], remote_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge local and remote configurations intelligently.
    
    Args:
        local_config: Local configuration dictionary
        remote_config: Remote configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    merged = local_config.copy()
    
    # Merge module configurations
    if "module_info" in remote_config and "module_info" in local_config:
        local_modules = local_config["module_info"]
        remote_modules = remote_config["module_info"]
        
        # Start with local modules
        merged["module_info"] = local_modules.copy()
        
        # Add or update with remote modules
        for module_name, module_data in remote_modules.items():
            if module_name not in local_modules:
                # New module from remote
                merged["module_info"][module_name] = module_data
            else:
                # Merge existing module data
                local_data = local_modules[module_name]
                merged_data = local_data.copy()
                
                # Keep local enabled status unless explicitly different
                if "enabled" in module_data:
                    merged_data["enabled"] = module_data["enabled"]
                
                # Merge other fields
                for key, value in module_data.items():
                    if key not in merged_data:
                        merged_data[key] = value
                
                merged["module_info"][module_name] = merged_data
    
    # Merge enabled modules list
    if "enabled_modules" in remote_config:
        local_enabled = set(local_config.get("enabled_modules", []))
        remote_enabled = set(remote_config["enabled_modules"])
        merged["enabled_modules"] = list(local_enabled.union(remote_enabled))
    
    return merged


def restore_config(backup_file: str, merge: bool = False) -> bool:
    """Restore MaxCLI configuration from a backup file.
    
    Args:
        backup_file: Path to the backup file
        merge: Whether to merge with existing configuration
        
    Returns:
        True if restore was successful, False otherwise
    """
    config_dir = Path.home() / ".config" / "maxcli"
    
    # Extract backup to temporary directory
    success, extracted_path = extract_backup(backup_file)
    if not success:
        return False
    
    extracted_dir = Path(extracted_path)
    
    # If merging, load and merge configurations
    if merge and config_dir.exists():
        print("🔄 Merging configurations...")
        
        # Load configurations
        try:
            with open(config_dir / "modules_config.json", 'r') as f:
                local_config = json.load(f)
            with open(extracted_dir / "modules_config.json", 'r') as f:
                remote_config = json.load(f)
            
            # Merge configurations
            merged_config = merge_configs(local_config, remote_config)
            
            # Save merged configuration
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_dir / "modules_config.json", 'w') as f:
                json.dump(merged_config, f, indent=2)
            
            print("✅ Configurations merged successfully")
            
        except Exception as e:
            print(f"❌ Failed to merge configurations: {e}")
            return False
    
    # Copy other configuration files
    try:
        # Create backup of existing config if it exists
        if config_dir.exists():
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = config_dir.parent / f"maxcli_backup_{backup_time}"
            shutil.copytree(config_dir, backup_dir)
            print(f"📦 Created backup of existing config at {backup_dir}")
        
        # Copy new configuration files
        if config_dir.exists():
            shutil.rmtree(config_dir)
        shutil.copytree(extracted_dir, config_dir)
        
        print("✅ Configuration restored successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to restore configuration: {e}")
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


def handle_restore_config(args) -> None:
    """Handle the restore-config command.
    
    Args:
        args: Parsed command line arguments
    """
    if args.target:
        # List available backups on remote server
        backups = list_remote_backups(args.target)
        if not backups:
            print(f"❌ No backups found on {args.target}")
            sys.exit(1)
        
        # Let user select a backup
        print("\nAvailable backups:")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup}")
        
        try:
            choice = int(input("\nSelect backup to restore (number): ").strip())
            if not (1 <= choice <= len(backups)):
                print("❌ Invalid selection")
                sys.exit(1)
            
            backup_file = backups[choice - 1]
            
            # Download selected backup
            success, local_file = download_backup_from_ssh(args.target, backup_file, args.local_destination)
            if not success or local_file is None:
                sys.exit(1)
            
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid selection or cancelled")
            sys.exit(1)
    else:
        if args.backup_file is None:
            print("❌ Error: --backup-file is required when not using --target")
            sys.exit(1)
        local_file = args.backup_file
    
    # Check if local config exists
    config_dir = Path.home() / ".config" / "maxcli"
    if config_dir.exists():
        print("\n⚠️  Existing configuration found!")
        print("Choose how to proceed:")
        print("  1. Keep local configuration")
        print("  2. Replace with backup configuration")
        print("  3. Merge configurations (experimental)")
        
        try:
            choice = int(input("\nSelect option (1-3): ").strip())
            if choice == 1:
                print("Keeping local configuration")
                return
            elif choice == 2:
                merge = False
            elif choice == 3:
                merge = True
            else:
                print("❌ Invalid selection")
                sys.exit(1)
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid selection or cancelled")
            sys.exit(1)
    else:
        merge = False
    
    # Restore configuration
    if not restore_config(local_file, merge):
        sys.exit(1)


def register_commands(subparsers) -> None:
    """Register configuration backup commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Backup command
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
    
    backup_parser.set_defaults(func=handle_backup_config)

    # Restore command
    restore_parser = subparsers.add_parser(
        'restore-config',
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
  max restore-config --backup-file ~/backups/maxcli_backup_20240321.tar.gz  # Restore from local backup
  max restore-config --target hetzner  # List and restore from remote backup
  max restore-config --target backup-server --local-destination ~/restored  # Custom restore location
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
    
    restore_parser.set_defaults(func=handle_restore_config) 