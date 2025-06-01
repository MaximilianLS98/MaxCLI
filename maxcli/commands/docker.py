"""Docker related commands."""
import sys
import subprocess


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
    - Recent containers (only removes containers stopped >24h ago)
    - Volumes (never touches volumes)
    """
    print("🧹 Performing minimal Docker cleanup...")
    
    try:
        # Remove containers that have been stopped for more than 24 hours
        print("Removing containers stopped >24h ago...")
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


# Legacy functions for backward compatibility during transition
def docker_clean(_args):
    """Legacy function for backward compatibility."""
    docker_clean_extensive()


def docker_tidy(_args):
    """Legacy function for backward compatibility."""
    docker_clean_minimal() 