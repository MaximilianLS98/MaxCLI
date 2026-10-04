import sys
"""SSH backup file transfer functionality using rsync over SSH.

This module provides secure file transfer capabilities for SSH backup files,
allowing upload and download of encrypted SSH key backups to/from remote servers
using rsync over SSH with existing SSH target configurations.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any

# Import from ssh_manager module
from .ssh_manager import load_ssh_targets as _load_ssh_targets


# Configuration constants
from maxcli.paths import config_dir

CONFIG_DIR = config_dir()
SSH_TARGETS_FILE = CONFIG_DIR / "ssh_targets.json"
BACKUP_FILENAME = "ssh_keys_backup.tar.gz.gpg"
LOCAL_BACKUP_PATH = Path.home() / BACKUP_FILENAME
REMOTE_BACKUP_DIR = "~/backups"
REMOTE_BACKUP_PATH = f"{REMOTE_BACKUP_DIR}/{BACKUP_FILENAME}"


def load_ssh_targets() -> Dict[str, Dict[str, Any]]:
    """Load SSH targets from the JSON configuration file.
    
    Returns:
        Dictionary of SSH targets, empty dict if file doesn't exist or is invalid.
    """
    if not SSH_TARGETS_FILE.exists():
        return {}
    
    try:
        with open(SSH_TARGETS_FILE, 'r') as f:
            content = json.load(f)
            return content if isinstance(content, dict) else {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load SSH targets file: {e}", file=sys.stderr)
        return {}


def get_ssh_target(target_name: str) -> Optional[Dict[str, Any]]:
    """Get SSH target configuration by name.
    
    Args:
        target_name: Name of the SSH target to retrieve
        
    Returns:
        SSH target configuration dict or None if not found
    """
    targets = load_ssh_targets()
    
    if not targets:
        print("Error: No SSH targets configured. Use 'max ssh add-target' to create one first.", file=sys.stderr)
        return None
    
    if target_name not in targets:
        print(f"Error: SSH target '{target_name}' not found.", file=sys.stderr)
        print("\nAvailable targets:")
        for name in sorted(targets.keys()):
            target = targets[name]
            print(f"  • {name} ({target['user']}@{target['host']}:{target.get('port', 22)})")
        return None
    
    return targets[target_name]


def create_remote_backup_directory(target: Dict) -> bool:
    """Create the backup directory on the remote server if it doesn't exist.
    
    Args:
        target: SSH target configuration dict
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    # Build SSH command to create directory
    ssh_cmd = [
        "ssh",
        "-i", target["key"],
        "-p", str(target.get("port", 22)),
        f"{target['user']}@{target['host']}",
        f"mkdir -p {REMOTE_BACKUP_DIR}"
    ]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"Warning: Could not create remote backup directory: {result.stderr.strip()}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("Error: SSH connection timed out while creating backup directory", file=sys.stderr)
        return False
    except subprocess.SubprocessError as e:
        print(f"Error: Failed to create remote backup directory: {e}", file=sys.stderr)
        return False


def rsync_upload_backup(target_name: str) -> bool:
    """Upload encrypted SSH backup to a remote server using rsync over SSH.
    
    Args:
        target_name: Name of the SSH target to upload to
        
    Returns:
        True if upload successful, False otherwise
    """
    print(f"🔄 Uploading SSH backup to '{target_name}'...")
    
    # Get SSH target configuration
    target = get_ssh_target(target_name)
    if not target:
        return False
    
    # Check if local backup file exists
    if not LOCAL_BACKUP_PATH.exists():
        print(f"Error: Local backup file not found: {LOCAL_BACKUP_PATH}", file=sys.stderr)
        print("Create a backup first using: max ssh export-keys")
        return False
    
    print(f"📁 Local backup file: {LOCAL_BACKUP_PATH} ({LOCAL_BACKUP_PATH.stat().st_size} bytes)")
    
    # Create remote backup directory
    print(f"📂 Ensuring remote backup directory exists...")
    if not create_remote_backup_directory(target):
        print("Continuing anyway - directory might already exist...")
    
    # Build rsync command
    ssh_options = f"ssh -i {target['key']} -p {target.get('port', 22)}"
    remote_destination = f"{target['user']}@{target['host']}:{REMOTE_BACKUP_PATH}"
    
    rsync_cmd = [
        "rsync",
        "-avz",
        "--progress",
        "-e", ssh_options,
        str(LOCAL_BACKUP_PATH),
        remote_destination
    ]
    
    print(f"🚀 Uploading to {target['user']}@{target['host']}:{target.get('port', 22)}...")
    print(f"📤 Command: {' '.join(rsync_cmd[:3])} -e '{ssh_options}' {LOCAL_BACKUP_PATH.name} {remote_destination}")
    
    try:
        result = subprocess.run(
            rsync_cmd,
            timeout=300  # 5 minute timeout for upload
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully uploaded SSH backup to '{target_name}'")
            print(f"📍 Remote location: {REMOTE_BACKUP_PATH}")
            return True
        else:
            print(f"❌ Upload failed with exit code: {result.returncode}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Upload timed out (5 minute limit exceeded)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("❌ Error: rsync command not found. Please install rsync.", file=sys.stderr)
        return False
    except subprocess.SubprocessError as e:
        print(f"❌ Upload failed: {e}", file=sys.stderr)
        return False


def check_remote_backup_exists(target: Dict) -> bool:
    """Check if backup file exists on the remote server.
    
    Args:
        target: SSH target configuration dict
        
    Returns:
        True if backup file exists on remote server, False otherwise
    """
    # Build SSH command to check if file exists
    ssh_cmd = [
        "ssh",
        "-i", target["key"],
        "-p", str(target.get("port", 22)),
        f"{target['user']}@{target['host']}",
        f"test -f {REMOTE_BACKUP_PATH}"
    ]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Warning: SSH connection timed out while checking remote file", file=sys.stderr)
        return False
    except subprocess.SubprocessError:
        return False


def rsync_download_backup(target_name: str) -> bool:
    """Download encrypted SSH backup from a remote server using rsync over SSH.
    
    Args:
        target_name: Name of the SSH target to download from
        
    Returns:
        True if download successful, False otherwise
    """
    print(f"🔄 Downloading SSH backup from '{target_name}'...")
    
    # Get SSH target configuration
    target = get_ssh_target(target_name)
    if not target:
        return False
    
    # Check if remote backup file exists
    print(f"🔍 Checking if backup exists on remote server...")
    if not check_remote_backup_exists(target):
        print(f"Error: Backup file not found on remote server: {REMOTE_BACKUP_PATH}", file=sys.stderr)
        print(f"Upload a backup first using: max rsync-upload-backup {target_name}")
        return False
    
    print(f"📁 Remote backup found: {REMOTE_BACKUP_PATH}")
    
    # Warn about local file overwrite
    if LOCAL_BACKUP_PATH.exists():
        local_size = LOCAL_BACKUP_PATH.stat().st_size
        print(f"⚠️  Local backup file will be overwritten: {LOCAL_BACKUP_PATH} ({local_size} bytes)")
    
    # Build rsync command
    ssh_options = f"ssh -i {target['key']} -p {target.get('port', 22)}"
    remote_source = f"{target['user']}@{target['host']}:{REMOTE_BACKUP_PATH}"
    
    rsync_cmd = [
        "rsync",
        "-avz",
        "--progress",
        "-e", ssh_options,
        remote_source,
        str(Path.home())
    ]
    
    print(f"🚀 Downloading from {target['user']}@{target['host']}:{target.get('port', 22)}...")
    print(f"📥 Command: {' '.join(rsync_cmd[:3])} -e '{ssh_options}' {remote_source} ~/")
    
    try:
        result = subprocess.run(
            rsync_cmd,
            timeout=300  # 5 minute timeout for download
        )
        
        if result.returncode == 0:
            if LOCAL_BACKUP_PATH.exists():
                local_size = LOCAL_BACKUP_PATH.stat().st_size
                print(f"✅ Successfully downloaded SSH backup from '{target_name}'")
                print(f"📍 Local location: {LOCAL_BACKUP_PATH} ({local_size} bytes)")
                print(f"💡 Import keys using: max ssh import-keys")
                return True
            else:
                print(f"❌ Download appeared successful but file not found locally", file=sys.stderr)
                return False
        else:
            print(f"❌ Download failed with exit code: {result.returncode}", file=sys.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Download timed out (5 minute limit exceeded)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("❌ Error: rsync command not found. Please install rsync.", file=sys.stderr)
        return False
    except subprocess.SubprocessError as e:
        print(f"❌ Download failed: {e}", file=sys.stderr)
        return False


# CLI handler functions
def handle_rsync_upload_backup(args) -> bool:
    """CLI handler for rsync-upload-backup command."""
    return rsync_upload_backup(args.target)


def handle_rsync_download_backup(args) -> bool:
    """CLI handler for rsync-download-backup command."""
    return rsync_download_backup(args.target)
