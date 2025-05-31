"""Docker related commands."""
import sys
import subprocess

def docker_clean(_args):
    """Perform aggressive Docker cleanup."""
    print("Cleaning up Docker system...")
    try:
        subprocess.run(["docker", "system", "prune", "-af"], check=True)
        print("✅ Docker cleanup completed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Docker cleanup: {e}", file=sys.stderr)
        sys.exit(1)

def docker_tidy(_args):
    """
    Perform a gentle Docker cleanup that only removes truly unused items.
    
    This is a safer alternative to docker-clean that preserves:
    - All images that might be reused
    - Recent containers (only removes containers stopped >24h ago)
    - Volumes (never touches volumes)
    """
    print("Performing gentle Docker cleanup...")
    
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
        
        print("✅ Gentle Docker cleanup completed!")
        print("💡 For aggressive cleanup, use 'max docker-clean'")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during Docker cleanup: {e}", file=sys.stderr)
        sys.exit(1) 