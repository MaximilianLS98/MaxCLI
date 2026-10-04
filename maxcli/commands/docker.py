"""Docker related commands."""
import sys
import subprocess
import shlex
from ..runtime import CommandError, prompt_input


def docker_clean_extensive() -> None:
    """Perform aggressive Docker cleanup."""
    print("🧹 Performing extensive Docker cleanup...")
    try:
        subprocess.run(["docker", "system", "prune", "-af"], check=True)
        print("✅ Extensive Docker cleanup completed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Docker cleanup: {e}", file=sys.stderr)
        sys.exit(1)


def docker_clean_minimal() -> None:
    """
    Perform a gentle Docker cleanup that only removes truly unused items.
    
    This is a safer alternative to extensive cleanup that preserves:
    - All images that might be reused
    - Recent containers (only removes stopped containers created >24h ago)
    - Volumes (never touches volumes)
    """
    print("🧹 Performing minimal Docker cleanup...")
    
    try:
        # Remove stopped containers created more than 24 hours ago
        print("Removing stopped containers created >24h ago...")
        subprocess.run([
            "docker", "container", "prune", "-f", 
            "--filter", "until=24h"
        ], check=True)
        
        # Remove only dangling images (untagged/unreferenced)
        print("Removing dangling images...")
        subprocess.run([
            "docker", "image", "prune", "-f"
        ], check=True)
        
        # Remove unused networks
        print("Removing unused networks...")
        subprocess.run([
            "docker", "network", "prune", "-f"
        ], check=True)
        
        # Remove build cache older than 7 days
        print("Removing build cache >7 days old...")
        subprocess.run([
            "docker", "builder", "prune", "-f",
            "--filter", "until=168h"  # 7 days = 168 hours
        ], check=True)
        
        print("✅ Minimal Docker cleanup completed!")
        print("💡 For extensive cleanup, use 'max docker clean --extensive'")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Docker cleanup: {e}", file=sys.stderr)
        sys.exit(1)


def docker_clean_command(args) -> None:
    """
    Handle the docker clean command with appropriate cleanup level.
    
    Args:
        args: Parsed command arguments containing cleanup level flags.
    """
    commands = [['docker', 'system', 'prune', '-af']] if args.extensive else [
        ['docker', 'container', 'prune', '-f', '--filter', 'until=24h'],
        ['docker', 'image', 'prune', '-f'], ['docker', 'network', 'prune', '-f'],
        ['docker', 'builder', 'prune', '-f', '--filter', 'until=168h']]
    if getattr(args, 'dry_run', False):
        print('Cleanup commands (no volumes are removed):')
        for command in commands:
            print(shlex.join(command))
        return
    if not getattr(args, 'yes', False):
        if prompt_input('Remove unused Docker resources? [y/N]: ').lower() not in ('y', 'yes'):
            raise CommandError('Docker cleanup cancelled')
    # Determine cleanup level - extensive takes precedence if both are set
    if args.extensive:
        docker_clean_extensive()
    elif args.minimal:
        docker_clean_minimal()
    else:
        # Default to minimal for safety
        print("⚠️  No cleanup level specified, defaulting to minimal cleanup.")
        print("   Use --extensive for aggressive cleanup or --minimal for explicit minimal cleanup.")
        docker_clean_minimal()




# Backwards-compatible Python entry points.
def docker_clean(args):
    docker_clean_extensive()


def docker_tidy(args):
    docker_clean_minimal()
