"""Kubernetes related commands."""
import subprocess

def kctx(args):
    """Switch Kubernetes context."""
    print(f"Switching Kubernetes context to '{args.context}'...")
    subprocess.run(["kubectl", "config", "use-context", args.context], check=True)
    print(f"✅ Switched to context: {args.context}") 